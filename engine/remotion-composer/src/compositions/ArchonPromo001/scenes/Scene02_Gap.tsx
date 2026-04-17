import React from 'react';
import {useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {KenBurns} from '../../../components/KenBurns';
import {FadeTransition} from '../../../components/SceneTransition';

// Scene 2: "La brecha competitiva" — 12s to 22s (frames 360–660)
// Split visual: slow/manual vs fast/automated. No text overlay (narration carries it).
interface Props {
  imagePath: string;
}

export const Scene02_Gap: React.FC<Props> = ({imagePath}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, width} = useVideoConfig();

  // Subtle dividing line animation
  const lineOpacity = interpolate(frame, [15, 45], [0, 0.8], {extrapolateRight: 'clamp'});

  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
      <KenBurns imageSrc={imagePath} mode="parallax_right" durationFrames={durationInFrames} />

      {/* Vertical accent divider */}
      <div
        style={{
          position: 'absolute',
          top: '10%',
          left: '50%',
          width: 3,
          height: '80%',
          background: 'linear-gradient(to bottom, transparent, #3E92CC, transparent)',
          opacity: lineOpacity,
          transform: 'translateX(-50%)',
        }}
      />

      <FadeTransition direction="in" durationFrames={15} />
      <FadeTransition direction="out" durationFrames={15} />
    </div>
  );
};
