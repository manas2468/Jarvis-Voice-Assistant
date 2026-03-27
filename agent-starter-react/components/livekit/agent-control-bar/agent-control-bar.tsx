'use client';

import * as React from 'react';
import { useCallback } from 'react';
import { Track } from 'livekit-client';
import { BarVisualizer, useRemoteParticipants } from '@livekit/components-react';
import { ChatTextIcon, PhoneDisconnectIcon } from '@phosphor-icons/react/dist/ssr';
import { ChatInput } from '@/components/livekit/chat/chat-input';
import { Button } from '@/components/ui/button';
import { Toggle } from '@/components/ui/toggle';
import { AppConfig } from '@/lib/types';
import { cn } from '@/lib/utils';
import { DeviceSelect } from '../device-select';
import { TrackToggle } from '../track-toggle';
import { UseAgentControlBarProps, useAgentControlBar } from './hooks/use-agent-control-bar';

export interface AgentControlBarProps
  extends React.HTMLAttributes<HTMLDivElement>,
    UseAgentControlBarProps {
  capabilities: Pick<AppConfig, 'supportsChatInput' | 'supportsVideoInput' | 'supportsScreenShare'>;
  onChatOpenChange?: (open: boolean) => void;
  onSendMessage?: (message: string) => Promise<void>;
  onDisconnect?: () => void;
  onDeviceError?: (error: { source: Track.Source; error: Error }) => void;
}

export function AgentControlBar({
  controls,
  saveUserChoices = true,
  capabilities,
  className,
  onSendMessage,
  onChatOpenChange,
  onDisconnect,
  onDeviceError,
  ...props
}: AgentControlBarProps) {
  const participants = useRemoteParticipants();
  const [chatOpen, setChatOpen] = React.useState(false);
  const [isSendingMessage, setIsSendingMessage] = React.useState(false);

  const isAgentAvailable = participants.some((p) => p.isAgent);
  const isInputDisabled = !chatOpen || !isAgentAvailable || isSendingMessage;

  const [isDisconnecting, setIsDisconnecting] = React.useState(false);

  const {
    micTrackRef,
    visibleControls,
    cameraToggle,
    microphoneToggle,
    screenShareToggle,
    handleAudioDeviceChange,
    handleVideoDeviceChange,
    handleDisconnect,
  } = useAgentControlBar({
    controls,
    saveUserChoices,
  });

  const handleSendMessage = async (message: string) => {
    setIsSendingMessage(true);
    try {
      await onSendMessage?.(message);
    } finally {
      setIsSendingMessage(false);
    }
  };

  const onLeave = async () => {
    setIsDisconnecting(true);
    await handleDisconnect();
    setIsDisconnecting(false);
    onDisconnect?.();
  };

  React.useEffect(() => {
    onChatOpenChange?.(chatOpen);
  }, [chatOpen, onChatOpenChange]);

  const onMicrophoneDeviceSelectError = useCallback((error: Error) => {
    onDeviceError?.({ source: Track.Source.Microphone, error });
  }, [onDeviceError]);

  return (
    <div
      aria-label="Voice assistant controls"
      className={cn(
        /* MAIN CONTAINER: Pure Stark HUD Glass */
        'bg-black/30 backdrop-blur-3xl border border-cyan-500/20 flex flex-col rounded-2xl p-3',
        'shadow-[0_0_30px_rgba(31,213,249,0.1)] transition-all duration-700 hover:border-cyan-500/40',
        className
      )}
      {...props}
    >
      {/* CHAT INPUT AREA */}
      {capabilities.supportsChatInput && (
        <div
          inert={!chatOpen}
          className={cn(
            'overflow-hidden transition-[all] duration-500 ease-in-out',
            chatOpen ? 'h-[57px] opacity-100' : 'h-0 opacity-0'
          )}
        >
          <div className="flex h-8 w-full group items-center">
            <ChatInput 
              onSend={handleSendMessage} 
              disabled={isInputDisabled} 
              className="w-full !bg-transparent !border-none text-cyan-300 placeholder:text-cyan-900 font-mono text-sm outline-none" 
            />
          </div>
          <hr className="border-cyan-500/10 my-3" />
        </div>
      )}

      {/* BUTTONS ROW */}
      <div className="flex flex-row justify-between gap-2">
        <div className="flex gap-2">
          
          {/* MICROPHONE SECTION */}
          {visibleControls.microphone && (
            <div className="flex items-center rounded-lg bg-cyan-500/5 border border-cyan-500/10 hover:bg-cyan-500/10 transition-colors">
              <TrackToggle
                source={Track.Source.Microphone}
                pressed={microphoneToggle.enabled}
                onPressedChange={microphoneToggle.toggle}
                className="!bg-transparent !border-none !text-cyan-400 p-2"
              >
                <BarVisualizer
                  barCount={5}
                  trackRef={micTrackRef}
                  options={{ minHeight: 4 }}
                  className="flex items-center gap-0.5"
                />
              </TrackToggle>
              <DeviceSelect
                kind="audioinput"
                onActiveDeviceChange={handleAudioDeviceChange}
                className="!bg-transparent !border-none !text-cyan-500/50 hover:!text-cyan-400 transition-colors pr-2"
              />
            </div>
          )}

          {/* CAMERA SECTION */}
          {capabilities.supportsVideoInput && visibleControls.camera && (
            <div className="flex items-center rounded-lg bg-cyan-500/5 border border-cyan-500/10 hover:bg-cyan-500/10">
              <TrackToggle
                source={Track.Source.Camera}
                pressed={cameraToggle.enabled}
                onPressedChange={cameraToggle.toggle}
                className="!bg-transparent !border-none !text-cyan-400"
              />
              <DeviceSelect
                kind="videoinput"
                onActiveDeviceChange={handleVideoDeviceChange}
                className="!bg-transparent !border-none !text-cyan-500/50 hover:!text-cyan-400 pr-2"
              />
            </div>
          )}

          {/* CHAT TOGGLE */}
          {visibleControls.chat && (
            <Toggle
              pressed={chatOpen}
              onPressedChange={setChatOpen}
              className={cn(
                "w-12 h-10 border transition-all duration-300",
                chatOpen 
                  ? "bg-cyan-500/20 border-cyan-400 text-cyan-400 shadow-[0_0_10px_rgba(31,213,249,0.3)]" 
                  : "bg-transparent border-white/10 text-white/40 hover:text-white"
              )}
            >
              <ChatTextIcon weight="bold" size={20} />
            </Toggle>
          )}
        </div>

        {/* DISCONNECT BUTTON */}
        {visibleControls.leave && (
          <Button
            onClick={onLeave}
            disabled={isDisconnecting}
            className={cn(
              "font-mono bg-red-500/10 border border-red-500/30 text-red-500",
              "hover:bg-red-500 hover:text-white hover:shadow-[0_0_15px_rgba(239,68,68,0.4)]",
              "transition-all duration-300 rounded-lg px-6"
            )}
          >
            <PhoneDisconnectIcon weight="bold" className="mr-2" />
            <span className="tracking-[0.2em] text-[10px] uppercase font-black">Terminate</span>
          </Button>
        )}
      </div>
    </div>
  );
}