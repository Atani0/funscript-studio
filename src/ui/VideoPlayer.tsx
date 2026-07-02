import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react';
import { formatTime } from '../app/video_controller';

export interface VideoPlayerHandle {
  seek(ms: number): void;
  toggle(): void;
  play(): void;
  pause(): void;
  step(frames: number): void;
}

interface Props {
  src?: string;
  playing: boolean;
  onPlayingChange(playing: boolean): void;
  onTime(ms: number): void;
  onDuration(ms: number): void;
  onVideoSize?(width: number, height: number): void;
  onImportVideo?(): void;
  onVideoFileDrop?(file: File): void;
  onVideoContextMenu?(x: number, y: number): void;
  onEndedPlayback?(): void;
}

const isVideoFile = (file: File) =>
  file.type.startsWith('video/') || /\.(mp4|mkv|webm|mov|avi|m4v|flv|ts|m2ts|mts|vob|mpg|mpeg|wmv|asf)$/i.test(file.name);

export const VideoPlayer = forwardRef<VideoPlayerHandle, Props>(function VideoPlayer(
  { src, playing, onPlayingChange, onTime, onDuration, onVideoSize, onImportVideo, onVideoFileDrop, onVideoContextMenu, onEndedPlayback },
  ref,
) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const frameRequest = useRef<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    setError(null);
  }, [src]);

  const cancelFrameLoop = () => {
    if (frameRequest.current === null) return;
    if (videoRef.current && 'cancelVideoFrameCallback' in videoRef.current) {
      videoRef.current.cancelVideoFrameCallback(frameRequest.current);
    } else {
      cancelAnimationFrame(frameRequest.current);
    }
    frameRequest.current = null;
  };

  const startFrameLoop = () => {
    const video = videoRef.current;
    if (!video) return;
    cancelFrameLoop();
    const update = () => {
      onTime(video.currentTime * 1000);
      if (!video.paused) {
        frameRequest.current = requestAnimationFrame(update);
      }
    };
    update();
  };

  const handleDrop = (event: React.DragEvent<HTMLElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setDragging(false);
    const file = [...event.dataTransfer.files].find(isVideoFile);
    if (file) onVideoFileDrop?.(file);
  };

  const dragProps = {
    onDragEnter: (event: React.DragEvent<HTMLElement>) => {
      event.preventDefault();
      setDragging(true);
    },
    onDragOver: (event: React.DragEvent<HTMLElement>) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';
      setDragging(true);
    },
    onDragLeave: (event: React.DragEvent<HTMLElement>) => {
      if (event.currentTarget.contains(event.relatedTarget as Node | null)) return;
      setDragging(false);
    },
    onDrop: handleDrop,
  };

  useImperativeHandle(ref, () => ({
    seek(ms) {
      const video = videoRef.current;
      if (!video) return;
      const seconds = Math.max(0, ms / 1000);
      if (!Number.isFinite(seconds)) return;
      video.currentTime = seconds;
      onTime(ms);
    },
    toggle() {
      const video = videoRef.current;
      if (!video) {
        onImportVideo?.();
        return;
      }
      if (video.paused) void video.play();
      else video.pause();
    },
    play() {
      const video = videoRef.current;
      if (!video) {
        onImportVideo?.();
        return;
      }
      void video.play();
    },
    pause() {
      videoRef.current?.pause();
    },
    step(frames) {
      const video = videoRef.current;
      if (!video) return;
      video.pause();
      const duration = Number.isFinite(video.duration) ? video.duration : Number.POSITIVE_INFINITY;
      video.currentTime = Math.max(0, Math.min(duration, video.currentTime + frames / 30));
      onTime(video.currentTime * 1000);
    },
  }));

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (playing && video.paused) void video.play();
    if (!playing && !video.paused) video.pause();
  }, [playing]);

  useEffect(() => cancelFrameLoop, []);

  if (!src) {
    return (
      <button
        className={dragging ? 'video-empty video-empty-button dragging' : 'video-empty video-empty-button'}
        type="button"
        onClick={onImportVideo}
        {...dragProps}
      >
        <div className="empty-icon">▶</div>
        <strong>导入视频开始</strong>
        <span>支持 MP4 / MKV / WebM / FLV / TS / WMV 等常见格式</span>
        <em>点击这里选择视频，或直接把视频文件拖进来</em>
      </button>
    );
  }

  if (error) {
    return (
      <div className={dragging ? 'video-empty dragging' : 'video-empty'} {...dragProps}>
        <div className="empty-icon warning">!</div>
        <strong>视频加载失败</strong>
        <span>{error}</span>
        <button className="button secondary" type="button" onClick={onImportVideo}>重新导入视频</button>
      </div>
    );
  }

  return (
    <div className={dragging ? 'video-shell dragging' : 'video-shell'} {...dragProps}>
      <video
        ref={videoRef}
        src={src}
        onLoadedMetadata={event => {
          const durationSeconds = event.currentTarget.duration;
          const durationMs = Number.isFinite(durationSeconds) && durationSeconds > 0 ? durationSeconds * 1000 : 0;
          onDuration(durationMs);
          onVideoSize?.(event.currentTarget.videoWidth, event.currentTarget.videoHeight);
          onTime(0);
        }}
        onPlay={() => {
          onPlayingChange(true);
          startFrameLoop();
        }}
        onPause={() => {
          onPlayingChange(false);
          onTime((videoRef.current?.currentTime ?? 0) * 1000);
          cancelFrameLoop();
        }}
        onEnded={() => {
          onPlayingChange(false);
          onEndedPlayback?.();
        }}
        onError={event => {
          const mediaError = event.currentTarget.error;
          const message = mediaError?.message || '当前内置播放器无法解码这个视频格式；FLV/TS/WMV 会在本地自动生成临时 MP4 预览，请重新用“导入视频”选择原文件。';
          setError(message);
          onPlayingChange(false);
        }}
        onClick={() => {
          const video = videoRef.current;
          if (!video) return;
          if (video.paused) void video.play();
          else video.pause();
        }}
        onContextMenu={event => {
          event.preventDefault();
          onVideoContextMenu?.(event.clientX, event.clientY);
        }}
        style={{ objectFit: 'contain', objectPosition: 'center center' }}
      />
      <div className="video-time">{formatTime((videoRef.current?.currentTime ?? 0) * 1000)}</div>
      <div className="drop-hint">松开鼠标导入视频</div>
    </div>
  );
});
