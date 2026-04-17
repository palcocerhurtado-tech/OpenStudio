import React from 'react';
import {useVideoConfig} from 'remotion';
import {KenBurns} from '../../../components/KenBurns';
import {TextOverlay} from '../../../components/TextOverlay';
import {FadeTransition} from '../../../components/SceneTransition';

// Scene 7: "Por qué Archon — Trust signal" — 53s to 57s (frames 1590–1710)
interface Props {
  imagePath: string;
}

export const Scene07_Trust: React.FC<Props> = ({imagePath}) => {
  const {durationInFrames} = useVideoConfig();

  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
      <KenBurns imageSrc={imagePath} mode="static_hold" durationFrames={durationInFrames} />

      <div style={{position: 'absolute', inset: 0, background: 'rgba(5,21,46,0.55)'}} />

      <TextOverlay
        text="Soluciones a medida. Implementación local. Resultados medibles."
        style="body_large"
        position="center"
        inFrame={15}
        outFrame={durationInFrames - 10}
      />

      <FadeTransition direction="in" durationFrames={15} />
      <FadeTransition direction="out" durationFrames={15} />
    </div>
  );
};
