import React from 'react';
import {useVideoConfig} from 'remotion';
import {KenBurns} from '../../../components/KenBurns';
import {TextOverlay} from '../../../components/TextOverlay';
import {FadeTransition} from '../../../components/SceneTransition';

// Scene 3: "Quiénes somos — Archon" — 22s to 32s (frames 660–960)
// Zaragoza skyline + AI overlay. Brand name + location reveal.
interface Props {
  imagePath: string;
}

export const Scene03_Archon: React.FC<Props> = ({imagePath}) => {
  const {durationInFrames} = useVideoConfig();

  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
      <KenBurns imageSrc={imagePath} mode="ken_burns_out" durationFrames={durationInFrames} />

      {/* Gradient bar at bottom for text legibility */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '35%',
          background: 'linear-gradient(to top, rgba(5,21,46,0.85), transparent)',
        }}
      />

      {/* Accent rule */}
      <div
        style={{
          position: 'absolute',
          bottom: '24%',
          left: 80,
          width: 60,
          height: 4,
          background: '#3E92CC',
          borderRadius: 2,
        }}
      />

      <TextOverlay
        text="Archon Consultancies"
        style="h1"
        position="lower-third"
        inFrame={45}
        outFrame={durationInFrames - 10}
      />
      <TextOverlay
        text="Zaragoza · España"
        style="body"
        position="lower-third"
        inFrame={65}
        outFrame={durationInFrames - 10}
      />

      <FadeTransition direction="in" durationFrames={15} />
      <FadeTransition direction="out" durationFrames={15} />
    </div>
  );
};
