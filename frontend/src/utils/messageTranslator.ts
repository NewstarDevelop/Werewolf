/**
 * Message Translator for System Messages
 *
 * Translates Chinese system messages from backend to i18n keys or English text.
 * Uses regex patterns to match common message formats.
 */

import { TFunction } from 'i18next';

interface TranslationPattern {
  // Regex pattern to match Chinese message
  pattern: RegExp;
  // Function to generate translation key or direct translation
  translate: (match: RegExpMatchArray, t: TFunction) => string;
}

// Translation patterns for common system messages
const translationPatterns: TranslationPattern[] = [
  // Night phases
  {
    pattern: /第(\d+)天?夜晚降临[，,]?请沉睡[。.]?/,
    translate: (match, t) => t('game:system_messages.night_falls', { day: match[1] })
  },
  {
    pattern: /狼人队内讨论开始[。.]?/,
    translate: (_, t) => t('game:system_messages.werewolf_discussion_start')
  },
  {
    pattern: /狼人讨论结束[，,]?请选择击杀目标[。.]?/,
    translate: (_, t) => t('game:system_messages.werewolf_select_target')
  },
  {
    pattern: /狼人请选择击杀目标[。.]?/,
    translate: (_, t) => t('game:system_messages.werewolf_select_target')
  },
  {
    pattern: /预言家请选择查验目标[。.]?/,
    translate: (_, t) => t('game:system_messages.seer_select_target')
  },
  {
    pattern: /女巫请选择行动[。.]?/,
    translate: (_, t) => t('game:system_messages.witch_action')
  },

  // Day phases
  {
    pattern: /天亮了[，,]?昨晚是平安夜[。.]?/,
    translate: (_, t) => t('game:system_messages.day_peaceful')
  },
  {
    pattern: /天亮了[，,]?昨晚.*?(\d+)号.*?死了[。.]?/,
    translate: (match, t) => t('game:system_messages.day_death', { id: match[1] })
  },
  {
    pattern: /天亮了[。.]?/,
    translate: (_, t) => t('game:system_messages.day_breaks')
  },
  {
    pattern: /请从(\d+)号开始发言[。.]?/,
    translate: (match, t) => t('game:system_messages.speech_start', { id: match[1] })
  },
  {
    pattern: /请(\d+)号发言[。.]?/,
    translate: (match, t) => t('game:system_messages.speak_turn', { id: match[1] })
  },
  {
    pattern: /轮到你发言了/,
    translate: (_, t) => t('game:system_messages.your_turn')
  },

  // Voting
  {
    pattern: /投票环节开始[。.]?/,
    translate: (_, t) => t('game:system_messages.voting_start')
  },
  {
    pattern: /请进行投票[。.]?/,
    translate: (_, t) => t('game:system_messages.vote_please')
  },
  {
    pattern: /(\d+)号被放逐了[。.]?/,
    translate: (match, t) => t('game:system_messages.player_exiled', { id: match[1] })
  },
  {
    pattern: /今天是平票[，,]?没有人被放逐[。.]?/,
    translate: (_, t) => t('game:system_messages.vote_tie')
  },

  // Hunter
  {
    pattern: /(\d+)号是猎人[，,]?请选择开枪目标[。.]?/,
    translate: (match, t) => t('game:system_messages.hunter_shoot', { id: match[1] })
  },
  {
    pattern: /猎人请选择开枪目标[。.]?/,
    translate: (_, t) => t('game:system_messages.hunter_select_target')
  },

  // Game over
  {
    pattern: /游戏结束[，,]?好人胜利/,
    translate: (_, t) => t('game:system_messages.game_over_villager')
  },
  {
    pattern: /游戏结束[，,]?狼人胜利/,
    translate: (_, t) => t('game:system_messages.game_over_werewolf')
  },
  {
    pattern: /游戏结束/,
    translate: (_, t) => t('game:system_messages.game_over')
  },

  // Last words
  {
    pattern: /(\d+)号请留遗言[。.]?/,
    translate: (match, t) => t('game:system_messages.last_words', { id: match[1] })
  },

  // Generic patterns with numbers
  {
    pattern: /(\d+)号/,
    translate: (match, t) => t('common:player.seat', { id: match[1] })
  }
];

/**
 * Translate a system message from Chinese to the current language
 * @param message - Original message text
 * @param t - i18next translation function
 * @returns Translated message or original if no match found
 */
export function translateSystemMessage(message: string, t: TFunction): string {
  // Try to match against all patterns
  for (const { pattern, translate } of translationPatterns) {
    const match = message.match(pattern);
    if (match) {
      try {
        return translate(match, t);
      } catch (error) {
        console.warn('Translation failed for message:', message, error);
        // Continue to next pattern
      }
    }
  }

  // If no pattern matches, return original message
  return message;
}

/**
 * Batch translate multiple messages
 * @param messages - Array of message texts
 * @param t - i18next translation function
 * @returns Array of translated messages
 */
export function translateSystemMessages(messages: string[], t: TFunction): string[] {
  return messages.map(msg => translateSystemMessage(msg, t));
}
