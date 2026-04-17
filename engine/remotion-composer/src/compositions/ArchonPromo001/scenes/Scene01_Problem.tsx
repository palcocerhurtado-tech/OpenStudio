import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {KenBurns} from '../../../components/KenBurns';
import {TextOverlay} from '../../../components/TextOverlay';
import {FadeTransition} from '../../../components/SceneTransition';

// Scene 1: "El problema" — 0s to 12s (frames 0–360)
// Cluttered desk with paper documents. Three staggered text reveals.
interface Props {
  imagePath: string;
}

export const Scene01_Problem: React.FC<Props> = ({imagePath}) => {
  const {durationInFrames} = useVideoConfig();

  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
      <KenBurns imageSrc={imagePath} mode="ken_burns_in" durationFrames={durationInFrames}>
        {/* Dark overlay to ensure text legibility */}
        <div style={{position: 'absolute', inset: 0, background: 'rgba(5,21,46,0.45)'}} />
      </KenBurns>

      {/* Staggered problem labels */}
      <TextOverlay text="Documentos a mano." style="h2" position="center" inFrame={60} outFrame={135} />
      <TextOverlay text="Onboardings eternos." style="h2" position="center" inFrame={150} outFrame={225} />
      <TextOverlay text="Informes sin tiempo." style="h2" position="center" inFrame={240} outFrame={345} />

      {/* Fade in at start */}
      <FadeTransition direction="in" durationFrames={18} />
      {/* Fade out at end */}
      <FadeTransition direction="out" durationFrames={15} />
    </div>
  );
};
