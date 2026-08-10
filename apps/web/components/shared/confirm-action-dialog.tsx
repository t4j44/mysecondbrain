'use client';

import * as React from 'react';
import { ShieldAlert, AlertTriangle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ConfirmActionDialogProps {
  open: boolean;
  onOpenChange: (val: boolean) => void;
  title: string;
  description: string;
  confirmLabel?: string;
  onConfirm: () => void | Promise<void>;
  isDestructive?: boolean;
}

export function ConfirmActionDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = 'CONFIRM EXECUTION',
  onConfirm,
  isDestructive = true,
}: ConfirmActionDialogProps) {
  const [isLoading, setIsLoading] = React.useState(false);

  if (!open) return null;

  async function handleExecute() {
    setIsLoading(true);
    try {
      await onConfirm();
      onOpenChange(false);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-sm animate-in fade-in duration-150"
        onClick={() => !isLoading && onOpenChange(false)}
      />

      {/* Dialog Modal Box */}
      <div
        className="relative w-full max-w-md rounded-lg border border-[#3b1e5a] bg-[#0a0510] p-6 shadow-[0_10px_50px_rgba(0,0,0,0.9)] z-10 animate-in zoom-in-95 duration-150 font-sans"
        role="alertdialog"
        aria-modal="true"
      >
        <button
          onClick={() => !isLoading && onOpenChange(false)}
          className="absolute right-3 top-3 rounded-md p-1 text-muted-foreground hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex items-start space-x-3 mb-4">
          <div className={`inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border ${
            isDestructive ? 'bg-destructive/20 border-destructive text-red-400' : 'bg-[#00ff9d]/15 border-[#00ff9d] text-[#00ff9d]'
          }`}>
            {isDestructive ? <ShieldAlert className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold uppercase text-muted-foreground block">
              [ OPERATOR VERIFICATION REQUIRED ]
            </span>
            <h3 className="text-lg font-extrabold text-[#f7f4ea]">
              {title}
            </h3>
          </div>
        </div>

        <p className="text-sm text-muted-foreground leading-relaxed mb-6">
          {description}
        </p>

        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-border">
          <Button
            onClick={() => onOpenChange(false)}
            variant="outline"
            disabled={isLoading}
            className="font-mono text-xs"
          >
            ABORT
          </Button>
          <Button
            onClick={handleExecute}
            variant={isDestructive ? 'destructive' : 'default'}
            disabled={isLoading}
            className="font-mono text-xs font-bold"
          >
            {isLoading ? 'EXECUTING...' : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
