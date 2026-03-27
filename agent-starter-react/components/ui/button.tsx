import * as React from 'react';
import { type VariantProps, cva } from 'class-variance-authority';
import { Slot } from '@radix-ui/react-slot';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  [
    'text-[10px] font-black tracking-[0.2em] uppercase whitespace-nowrap font-mono',
    'inline-flex items-center justify-center gap-2 shrink-0 rounded-lg cursor-pointer outline-none transition-all duration-300',
    'disabled:pointer-events-none disabled:opacity-30',
    "[&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 [&_svg]:shrink-0",
  ],
  {
    variants: {
      variant: {
        /* JARVIS DEFAULT: Transparent Cyan Glass */
        default: [
          'bg-cyan-500/5 border border-cyan-500/20 text-cyan-400',
          'hover:bg-cyan-500/20 hover:border-cyan-500/50 hover:shadow-[0_0_15px_rgba(31,213,249,0.3)]',
        ],
        /* JARVIS DESTRUCTIVE: Red Glass */
        destructive: [
          'bg-red-500/10 border border-red-500/40 text-red-500',
          'hover:bg-red-500 hover:text-white hover:shadow-[0_0_20px_rgba(239,68,68,0.4)]',
        ],
        /* GHOST: Invisible until hover */
        ghost: 'text-cyan-500/60 hover:text-cyan-400 hover:bg-cyan-500/10',
        outline: 'border border-cyan-500/30 bg-transparent text-cyan-400 hover:bg-cyan-500/10',
        primary: 'bg-cyan-500/20 border border-cyan-500 text-cyan-400 shadow-[0_0_10px_rgba(31,213,249,0.2)]',
        secondary: 'bg-white/5 border border-white/10 text-white/70 hover:text-white hover:bg-white/10',
        link: 'text-cyan-400 underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 px-3 text-[9px]',
        lg: 'h-12 px-8 text-[11px]',
        icon: 'size-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot : 'button';

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };