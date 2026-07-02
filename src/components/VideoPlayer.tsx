import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';

export interface VideoPlayerHandle {
  seek(ms: number): void;
  toggle(): void;
  step(frames: number): void;
}

interface Props {
  src?: string;
  playing: boolean;
  onPlayingChange(playing: boolean): void;
  onTime(ms: number): void;
  onDuration(ms: number): void;
}

const formatTime = (ms: number) => {
  const totalSeconds = Math.max(0, ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  const millis = Math.floor(ms % 1000);
  return `${minutes}:${seconds.toString().padStart(2, '0')}.${millis.toString().padStart(3, '0')}`;
};

export const VideoPlayer = forwardRef<VideoPlayerHandle, Props>(function VideoPlayer(
  { src, playing, onPlayingChange, onTime, onDuration },
  ref
) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const frameRequest = useRef<number | null>(null);

  const startFrameLoop = () => {
    const video = videoRef.current;
    if (!video) return;
    const update = () => {
      onTime(video.currentTime * 1000);
      if (!video.paused) {
        if ('requestVideoFrameCallback' in video) {
          frameRequest.current = video.requestVideoFrameCallback(update);
        } else {
          frameRequest.current = requestAnimationFrame(update);
        }
      }
    };
    update();
  };

  useImperativeHandle(ref, () => ({
    seek(ms) {
      if (videoRef.current) {
        videoRef.current.currentTime = ms / 1000;
        onTime(ms);
      }
    },
    toggle() {
      const video = videoRef.current;
      if (!video) return;
      if (video.paused) void video.play();
      else video.pause();
    },
    step(frames) {
      const video = videoRef.current;
      if (!video) return;
      video.pause();
      video.currentTime = Math.max(0, Math.min(video.duration || Infinity, video.currentTime + frames / 30));
      onTime(video.currentTime * 1000);
    }
  }));

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (playing && video.paused) void video.play();
    if (!playing && !video.paused) video.pause();
  }, [playing]);

  useEffect(() => () => {
    if (frameRequest.current !== null) cancelAnimationFrame(frameRequest.current);
  }, []);

  if (!src) {
    return (
      <div className="video-empty">
        <div className="empty-icon">▶</div>
        <strong>导入视频开始</strong>
        <span>支持 MP4、MKV、WebM 等 Electron 可解码格式</span>
      </div>
    );
  }

  return (
    <div className="video-shell">
      <video
        ref={videoRef}
        src={src}
        onLoadedMetadata={event => onDuration(event.currentTarget.duration * 1000)}
        onPlay={() => {
          onPlayingChange(true);
          startFrameLoop();
        }}
        onPause={() => {
          onPlayingChange(false);
          onTime(videoRef.current?.currentTime ? videoRef.current.currentTime * 1000 : 0);
        }}
        onEnded={() => onPlayingChange(false)}
        onClick={() => ref && videoRef.current && (videoRef.current.paused ? void videoRef.current.play() : videoRef.current.pause())}
      />
      <div className="video-time">{formatTime((videoRef.current?.currentTime ?? 0) * 1000)}</div>
    </div>
  );
});
