'use client';

import { motion, AnimatePresence } from 'framer-motion';

interface JarvisRingsProps {
  expansion: number; // Value from 0.0 to ~2.0 based on hand distance
}

export const JarvisRings = ({ expansion }: JarvisRingsProps) => {
  // Only show the UI when the user starts spreading their palms
  const isVisible = expansion > 0.1;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 flex items-center justify-center pointer-events-none z-[100]"
        >
          {/* Subtle Cyberpunk Background Glow */}
          <div className="absolute inset-0 bg-cyan-950/10 backdrop-blur-[1px]" />

          {/* Core HUD Section */}
          <motion.div 
            animate={{ 
              scale: 0.8 + (expansion * 0.3),
              opacity: Math.min(1, expansion) 
            }}
            className="relative flex items-center justify-center"
          >
            <h1 className="text-cyan-400 font-black tracking-[0.7em] text-6xl drop-shadow-[0_0_15px_rgba(34,211,238,0.7)] z-50">
              JARVIS
            </h1>
            
            {/* Pulsing Energy Core */}
            <motion.div 
              animate={{ 
                scale: [1, 1.15, 1],
                opacity: [0.2, 0.4, 0.2] 
              }}
              transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
              className="absolute w-48 h-48 bg-cyan-400/20 rounded-full blur-3xl"
            />
          </motion.div>

          {/* Dynamic Concentric Data Rings */}
          {[1, 2, 3, 4, 5].map((ring, index) => (
            <motion.div
              key={ring}
              animate={{ 
                // Rings scale up as hands move apart
                scale: expansion * (0.7 + index * 0.45),
                // Alternate rotation direction for a mechanical feel
                rotate: expansion * (index % 2 === 0 ? 120 : -120),
                opacity: Math.max(0, 0.7 - (index * 0.12)),
              }}
              transition={{ 
                type: 'spring', 
                damping: 22, 
                stiffness: 90 
              }}
              style={{
                width: '550px',
                height: '550px',
                border: `${2 / ring}px solid rgba(34, 211, 238, ${0.7 / ring})`,
                boxShadow: `0 0 ${8 * ring}px rgba(6, 182, 212, 0.2)`,
              }}
              className="absolute rounded-full flex items-center justify-center"
            >
              {/* Internal HUD Details */}
              {index === 1 && (
                <div className="absolute inset-4 rounded-full border-t-4 border-cyan-400/20 border-dashed" />
              )}
              {index === 3 && (
                <div className="absolute inset-0 rounded-full border-l-2 border-r-2 border-cyan-300/10" />
              )}
            </motion.div>
          ))}

          {/* Telemetry Data Feed (Left Side) */}
          <motion.div 
            initial={{ x: -50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="absolute left-12 top-1/2 -translate-y-1/2 flex flex-col gap-2"
          >
            <div className="h-[2px] w-24 bg-cyan-500/50" />
            <div className="text-cyan-400 text-[10px] font-mono tracking-widest uppercase">
              <p>Biometric: Scanning</p>
              <p>Range: {Math.round(expansion * 100)}%</p>
              <p>Link: Secure</p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};