import React from 'react';
import {useVideoConfig} from 'remotion';
import {KenBurns} from '../../../components/KenBurns';
import {TextOverlay} from '../../../components/TextOverlay';
import {FadeTransition} from '../../../components/SceneTransition';

// Scene 4: "Caso 1 — Gestión Documental" — 32s to 39s (frames 960–1170)
interface Props {
  imagePath: string;
}

export const Scene04_Documents: React.FC<Props> = ({imagePath}) => {
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

      {/* Numbered use-case badge */}
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
        1
      </div>

      <TextOverlay
        text="Gestión Documental Automatizada"
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
