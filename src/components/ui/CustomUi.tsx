import React from 'react';
import { X } from 'lucide-react';

// --- Card Component ---
export const Card: React.FC<React.HTMLAttributes<HTMLDivElement> & { header?: React.ReactNode }> = ({
  children,
  className = '',
  header,
  ...props
}) => {
  return (
    <div
      className={`terminal-panel rounded-xl p-5 transition-all ${className}`}
      {...props}
    >
      {header && (
        <div className="border-b border-terminal-border pb-3 mb-4 flex items-center justify-between">
          {header}
        </div>
      )}
      {children}
    </div>
  );
};

// --- Button Component ---
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className = '',
  variant = 'outline',
  size = 'md',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-mono rounded-lg transition-all focus:outline-none focus:ring-1 focus:ring-terminal-accent active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none';
  
  const variants = {
    primary: 'bg-terminal-accent text-terminal-panel hover:bg-terminal-accentHover hover:shadow-[0_0_15px_rgba(0,255,157,0.3)] font-semibold border-1 border-terminal-accent',
    outline: 'border-1 border-terminal-border text-terminal-fg hover:border-terminal-accent hover:text-terminal-accent bg-transparent',
    ghost: 'text-terminal-fg hover:bg-terminal-fg/5 bg-transparent',
    destructive: 'border-1 border-terminal-alert text-terminal-alert hover:bg-terminal-alert/10 bg-transparent',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-2.5 text-base',
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

// --- Status Badge Component ---
export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const normStatus = status.toLowerCase();
  
  const styles: Record<string, string> = {
    // Venture
    active: 'border-terminal-accent/30 text-terminal-accent bg-terminal-accent/5',
    paused: 'border-terminal-warn/30 text-terminal-warn bg-terminal-warn/5',
    exited: 'border-terminal-muted text-terminal-muted bg-white/5',
    // Project
    planning: 'border-cyan-500/30 text-cyan-400 bg-cyan-500/5',
    in_progress: 'border-purple-500/30 text-purple-400 bg-purple-500/5',
    completed: 'border-terminal-accent/30 text-terminal-accent bg-terminal-accent/5',
    on_hold: 'border-terminal-warn/30 text-terminal-warn bg-terminal-warn/5',
    // Task
    todo: 'border-terminal-muted text-terminal-fg bg-transparent',
    done: 'border-terminal-accent/30 text-terminal-accent bg-terminal-accent/5 line-through opacity-60',
    cancelled: 'border-terminal-alert/30 text-terminal-alert bg-terminal-alert/5 opacity-50',
    archived: 'border-terminal-muted text-terminal-muted bg-white/5 opacity-50',
  };

  const labels: Record<string, string> = {
    in_progress: 'in progress',
    on_hold: 'on hold',
    todo: 'to do',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono border ${styles[normStatus] || 'border-terminal-border text-terminal-fg'}`}>
      {labels[normStatus] || normStatus}
    </span>
  );
};

// --- Priority Badge Component ---
export const PriorityBadge: React.FC<{ priority: string }> = ({ priority }) => {
  const normPriority = priority.toLowerCase();

  const styles: Record<string, string> = {
    low: 'text-terminal-muted border-terminal-border',
    medium: 'text-terminal-fg border-terminal-border',
    high: 'text-terminal-warn border-terminal-warn/30 bg-terminal-warn/5',
    urgent: 'text-terminal-alert border-terminal-alert/30 bg-terminal-alert/5 font-bold animate-pulse',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono border ${styles[normPriority] || 'border-terminal-border'}`}>
      {normPriority}
    </span>
  );
};

// --- Dialog Modal Component ---
interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const Dialog: React.FC<DialogProps> = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/70 backdrop-blur-sm" 
        onClick={onClose} 
      />
      
      {/* Dialog Content */}
      <div className="relative w-full max-w-lg terminal-panel rounded-xl overflow-hidden z-10 animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="border-b border-terminal-border px-5 py-4 flex items-center justify-between bg-terminal-panel">
          <h3 className="font-mono text-base font-bold text-terminal-accent uppercase tracking-wider">{title}</h3>
          <button 
            onClick={onClose}
            className="text-terminal-muted hover:text-terminal-accent transition-colors"
          >
            <X size={18} />
          </button>
        </div>
        
        {/* Body */}
        <div className="px-6 py-5 bg-terminal-bg max-h-[75vh] overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
};
