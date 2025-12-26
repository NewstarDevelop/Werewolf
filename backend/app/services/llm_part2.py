
    def generate_response(
        self,
        player: "Player",
        game: "Game",
        action_type: str,
        targets: list[int] = None,
    ) -> LLMResponse:
        """
        Generate AI response with retry and fallback.

        Args:
            player: The AI player
            game: Current game state
            action_type: Type of action (speech, vote, kill, verify, etc.)
            targets: Available target seat IDs for actions

        Returns:
            LLMResponse with thought, speak, and action_target
        """
        # Use mock mode if configured
        if self.use_mock:
            logger.info(f"Using mock response for player {player.seat_id}")
            return self._get_fallback_response(player, action_type, targets)

        # Get client for this player
        client, provider = self._get_client_for_player(player.seat_id)
        if not client or not provider:
            logger.warning(f"No LLM client available for player {player.seat_id}, using fallback")
            return self._get_fallback_response(player, action_type, targets)

        # Build prompts
        system_prompt = build_system_prompt(player, game)
        context_prompt = build_context_prompt(player, game, action_type)

        # Add wolf strategy for werewolves
        if player.role.value == "werewolf":
            strategy = build_wolf_strategy_prompt(player, game)
            if strategy:
                context_prompt = strategy + "
" + context_prompt

        # Try with retries and exponential backoff
        last_error = None
        max_retries = max(provider.max_retries, 4)  # At least 4 retries for rate limiting

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"LLM call attempt {attempt + 1} for player {player.seat_id} "
                    f"using provider {provider.name} (model: {provider.model})"
                )

                raw_response = self._call_llm(client, provider, system_prompt, context_prompt)
                response = self._parse_response(raw_response, provider.name)

                # Validate action_target if needed
                if action_type in ["vote", "kill", "verify", "shoot"]:
                    if response.action_target is not None and targets:
                        if response.action_target not in targets and response.action_target != 0:
                            logger.warning(
                                f"Invalid target {response.action_target}, expected one of {targets}"
                            )
                            response.action_target = random.choice(targets)

                logger.info(
                    f"LLM response for player {player.seat_id} from {provider.name}: "
                    f"{response.speak[:50]}..."
                )
                return response

            except Exception as e:
                last_error = e
                logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}")

                # Apply linear backoff for rate limiting (403 errors)
                # First retry: 60s, then add 60s each time, max 180s
                if "403" in str(e) or "blocked" in str(e).lower() or "rate" in str(e).lower():
                    delay = min(INITIAL_RETRY_DELAY + (BACKOFF_INCREMENT * attempt), MAX_RETRY_DELAY)
                    logger.info(f"Rate limited, waiting {delay}s before retry...")
                    time.sleep(delay)
                elif attempt < max_retries - 1:
                    # Short delay for other errors
                    time.sleep(2)

        # All retries failed, use fallback
        logger.error(f"All LLM retries failed for player {player.seat_id}: {last_error}")
        return self._get_fallback_response(player, action_type, targets)

    # ==================== Convenience Methods ====================

    def generate_speech(self, player: "Player", game: "Game") -> str:
        """Generate speech for an AI player."""
        response = self.generate_response(player, game, "speech")
        return response.speak

    def decide_kill_target(
        self, player: "Player", game: "Game", targets: list[int]
    ) -> int:
        """Decide who to kill as werewolf."""
        response = self.generate_response(player, game, "kill", targets)
        return response.action_target if response.action_target else random.choice(targets)

    def decide_verify_target(
        self, player: "Player", game: "Game", targets: list[int]
    ) -> int:
        """Decide who to verify as seer."""
        response = self.generate_response(player, game, "verify", targets)
        return response.action_target if response.action_target else random.choice(targets)

    def decide_witch_action(self, player: "Player", game: "Game") -> dict:
        """Decide witch action (save/poison)."""
        result = {"save": False, "poison_target": None}

        # First check if should save
        if player.has_save_potion and game.night_kill_target:
            response = self.generate_response(
                player, game, "witch_save", [game.night_kill_target, 0]
            )
            if response.action_target == game.night_kill_target:
                result["save"] = True
                return result  # Cannot use both in same night

        # Then check if should poison
        if player.has_poison_potion:
            alive_others = [
                p.seat_id for p in game.get_alive_players()
                if p.seat_id != player.seat_id
            ]
            if alive_others:
                response = self.generate_response(
                    player, game, "witch_poison", alive_others + [0]
                )
                if response.action_target and response.action_target != 0:
                    result["poison_target"] = response.action_target

        return result

    def decide_vote_target(
        self, player: "Player", game: "Game", targets: list[int]
    ) -> int:
        """Decide who to vote for."""
        response = self.generate_response(player, game, "vote", targets + [0])
        return response.action_target if response.action_target is not None else random.choice(targets)

    def decide_shoot_target(
        self, player: "Player", game: "Game", targets: list[int]
    ) -> Optional[int]:
        """Decide who to shoot as hunter."""
        response = self.generate_response(player, game, "shoot", targets + [0])
        if response.action_target and response.action_target != 0:
            return response.action_target
        return None

    # Legacy method for compatibility
    def generate_player_action(self, system_prompt: str, context: str) -> dict:
        """Legacy method - returns mock decision data."""
        return {
            "thought": "我是AI，正在思考中...",
            "speak": "我是AI，以后再说。",
            "action_target": None,
        }
