import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface WelcomeProps {
  disabled: boolean;
  startButtonText: string;
  onStartCall: () => void;
}

export const Welcome = ({
  disabled,
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeProps) => {
  return (
    <section
      ref={ref}
      inert={disabled}
      className={cn(
        'bg-background fixed inset-0 mx-auto flex h-svh flex-col items-center justify-center text-center',
        disabled ? 'z-10' : 'z-20'
      )}
    >
            <div className="relative inline-block">
        {/* GIF */}
        <img
          src="/Jarvis.gif"
          alt="Jarvis"
          className="w-[1000px] h-auto"
        />

        {/* Overlay content */}
        <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 text-center bg-black bg-opacity-70 px-6 py-4 rounded-lg inline-block">
  <Button
    variant="primary"
    size="lg"
    onClick={() => {
      // Play button click sound
      const clickSound = new Audio("/button-click.m4a");
      clickSound.volume = 0.3;
      clickSound.play();

      // Call your original function
      onStartCall();
    }}
    className="mt-4 w-100 font-mono"
  >
    {startButtonText}
  </Button>
</div>
      </div>
      <footer className="fixed bottom-5 left-0 z-20 flex w-full items-center justify-center">
  <div className="flex flex-col items-center gap-1">
    <div className="flex items-center gap-2">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
      </span>
      <p className="text-cyan-500/80 text-[10px] uppercase tracking-widest font-bold">
        System Online
      </p>
    </div>
    <p className="text-fg1 text-xs opacity-50">
      Built by <span className="font-semibold text-white">Created by Manas K  hadke</span>
    </p>
  </div>
</footer>
    </section>
  );
};
