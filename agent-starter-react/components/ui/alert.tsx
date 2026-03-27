import * as React from 'react';
import { type VariantProps, cva } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const alertVariants = cva(
  [
    /* UI UPGRADE: Added backdrop-blur and border-cyan for Jarvis look */
    'relative w-full rounded-lg border px-4 py-3 text-sm grid grid-cols-[0_1fr] gap-y-0.5 items-start transition-all duration-500',
    'backdrop-blur-xl bg-black/40 shadow-[0_0_15px_rgba(31,213,249,0.1)]',
    'has-[>svg]:grid-cols-[calc(var(--spacing)*4)_1fr] has-[>svg]:gap-x-3 [&>svg]:size-4 [&>svg]:translate-y-0.5 [&>svg]:text-current',
  ],
  {
    variants: {
      variant: {
        /* Default is now Cyan Jarvis Glass */
        default: 'border-cyan-500/30 text-cyan-400 [&>svg]:text-cyan-400',
        /* Destructive is now Red Jarvis Glass */
        destructive: [
          'border-red-500/40 text-red-500 bg-red-500/5 shadow-[0_0_15px_rgba(239,68,68,0.1)]',
          '[&>svg]:text-red-500 *:data-[slot=alert-description]:text-red-400/80',
        ],
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

function Alert({
  className,
  variant,
  ...props
}: React.ComponentProps<'div'> & VariantProps<typeof alertVariants>) {
  return (
    <div
      data-slot="alert"
      role="alert"
      className={cn(alertVariants({ variant }), className)}
      {...props}
    />
  );
}

function AlertTitle({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      data-slot="alert-title"
      className={cn('col-start-2 line-clamp-1 min-h-4 font-black tracking-[0.2em] uppercase text-[10px]', className)}
      {...props}
    />
  );
}

function AlertDescription({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      data-slot="alert-description"
      className={cn(
        'text-cyan-100/60 col-start-2 grid justify-items-start gap-1 text-[11px] font-mono [&_p]:leading-relaxed',
        className
      )}
      {...props}
    />
  );
}

export { Alert, AlertTitle, AlertDescription };