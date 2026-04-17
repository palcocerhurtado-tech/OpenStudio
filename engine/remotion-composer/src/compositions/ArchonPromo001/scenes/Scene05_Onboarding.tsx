import React from 'react';
import {useVideoConfig} from 'remotion';
import {KenBurns} from '../../../components/KenBurns';
import {TextOverlay} from '../../../components/TextOverlay';
import {FadeTransition} from '../../../components/SceneTransition';

// Scene 5: "Caso 2 — Onboarding de Clientes" — 39s to 46s (frames 1170–1380)
interface Props {
  imagePath: string;
}

export const Scene05_Onboarding: React.FC<Props> = ({imagePath}) => {
  const {durationInFrames} = useVideoConfig();

  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
      <KenBurns imageSrc={imagePath} mode="parallax_left" durationFrames={durationInFrames} />

      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '30%',
          background: 'linear-gradient(to top, rgba(5,21,46,0.80), transparent)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          bottom: '22%',
          left: 80,
          width: 44,
          height: 44,
          borderRadius: '50%',
          background: '#3E92CC',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 22,
          fontWeight: 700,
          color: '#fff',
          fontFamily: 'Inter, sans-serif',
        }}
      >
        2
      </div>

      <TextOverlay
        text="Onboarding de Clientes sin Fricciones"
        style="h2"
        position="lower-third"
        inFrame={20}
        outFrame={durationInFrames - 8}
      />

      <FadeTransition direction="in" durationFrames={15} />
      <FadeTransition direction="out" durationFrames={15} />
    </div>
  );
};
