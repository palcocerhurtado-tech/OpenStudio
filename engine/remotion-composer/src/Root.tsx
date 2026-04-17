import React from 'react';
import {Composition} from 'remotion';
import {ArchonPromo001} from './compositions/ArchonPromo001';
import {ArchonPromo001Vertical} from './compositions/ArchonPromo001Vertical';

// FPS: 30  |  16:9: 1920×1080  |  9:16: 1080×1920  |  Duration: 60s = 1800 frames

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="ArchonPromo001"
        component={ArchonPromo001}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />
      <Composition
        id="ArchonPromo001Vertical"
        component={ArchonPromo001Vertical}
        durationInFrames={1800}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{}}
      />
    </>
  );
};
