import React from 'react';
import {useVideoConfig} from 'remotion';
import {KenBurns} from '../../../components/KenBurns';
import {TextOverlay} from '../../../components/TextOverlay';
import {FadeTransition} from '../../../components/SceneTransition';

// Scene 6: "Caso 3 — Reporting Interno" — 46s to 53s (frames 1380–1590)
interface Props {
  imagePath: string;
}

export const Scene06_Reporting: React.FC<Props> = ({imagePath}) => {
  const {durationInFrames} = useVideoConfig();

  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
      <KenBurns imageSrc={imagePath} mode="ken_burns_in" durationFrames={durationInFrames} />

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
        3
      </div>

      <TextOverlay
        text="Reporting Inteligente en Tiempo Real"
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
