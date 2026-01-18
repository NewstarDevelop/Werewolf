/**
 * Environment Variables Table
 * Displays list of environment variables with segmented view (Pending/Configured)
 */

import { useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Edit, Trash2, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import { EnvVariable } from '@/types/config';

interface EnvVariablesTableProps {
  variables: EnvVariable[];
  onEdit: (variable: EnvVariable) => void;
  onDelete: (variable: EnvVariable) => void;
}

export function EnvVariablesTable({ variables, onEdit, onDelete }: EnvVariablesTableProps) {
  const [visibleValues, setVisibleValues] = useState<Set<string>>(new Set());

  const toggleVisibility = (name: string) => {
    setVisibleValues(prev => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  // Split variables into pending and configured
  const pendingVars = variables.filter(v => !v.is_set && v.is_required);
  const configuredVars = variables.filter(v => v.is_set);

  if (variables.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No environment variables found. Click "Add Variable" to create one.
      </div>
    );
  }

  const renderRow = (variable: EnvVariable, isPending: boolean) => {
    const isVisible = visibleValues.has(variable.name);
    const showValue = variable.is_sensitive ? (isVisible ? variable.value || '(empty)' : '********') : variable.value || '(empty)';

    return (
      <TableRow key={variable.name}>
        <TableCell className="font-mono font-semibold">
          <div className="flex items-center gap-2">
            {variable.name}
            {isPending && (
              <Badge variant="destructive" className="h-5 text-[10px]">
                Missing
              </Badge>
            )}
            {variable.is_sensitive && (
              <Badge variant="secondary" className="text-xs">
                Sensitive
              </Badge>
            )}
            {!isPending && variable.is_required && (
              <Badge variant="outline" className="text-xs">
                Required
              </Badge>
            )}
          </div>
        </TableCell>
        <TableCell>
          {isPending ? (
            <span className="italic text-muted-foreground text-sm">Required in .env.example</span>
          ) : (
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm truncate max-w-md">
                {showValue}
              </span>
              {variable.is_sensitive && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleVisibility(variable.name)}
                  className="h-6 w-6 p-0"
                >
                  {isVisible ? (
                    <EyeOff className="h-3 w-3" />
                  ) : (
                    <Eye className="h-3 w-3" />
                  )}
                </Button>
              )}
            </div>
          )}
        </TableCell>
        <TableCell className="text-right">
          <div className="flex items-center justify-end gap-2">
            {isPending ? (
              <Button
                size="sm"
                onClick={() => onEdit(variable)}
              >
                Configure
              </Button>
            ) : (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onEdit(variable)}
                  disabled={!variable.is_editable}
                  title={!variable.is_editable ? 'This variable cannot be edited via UI' : ''}
                >
                  <Edit className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDelete(variable)}
                  disabled={!variable.is_editable}
                  title={!variable.is_editable ? 'This variable cannot be deleted via UI' : ''}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </>
            )}
          </div>
        </TableCell>
      </TableRow>
    );
  };

  return (
    <div className="border rounded-md overflow-hidden">
      <Table>
        {/* Pending Configuration Section */}
        {pendingVars.length > 0 && (
          <>
            <TableHeader className="bg-yellow-50 dark:bg-yellow-950/30">
              <TableRow>
                <TableHead colSpan={3} className="text-yellow-700 dark:text-yellow-400 font-bold">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Pending Configuration ({pendingVars.length})
                  </div>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableHeader className="bg-yellow-50/50 dark:bg-yellow-950/10">
              <TableRow>
                <TableHead>Variable Name</TableHead>
                <TableHead>Value</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody className="bg-yellow-50/30 dark:bg-yellow-950/10">
              {pendingVars.map((variable) => renderRow(variable, true))}
            </TableBody>
          </>
        )}

        {/* Active Variables Section */}
        <TableHeader className="bg-muted/50">
          <TableRow>
            <TableHead colSpan={3} className="font-semibold">
              ✅ Active Variables
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableHeader>
          <TableRow>
            <TableHead>Variable Name</TableHead>
            <TableHead>Value</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {configuredVars.length > 0 ? (
            configuredVars.map((variable) => renderRow(variable, false))
          ) : (
            <TableRow>
              <TableCell colSpan={3} className="text-center py-8 text-muted-foreground">
                No configured variables. Configure the required variables above to get started.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
