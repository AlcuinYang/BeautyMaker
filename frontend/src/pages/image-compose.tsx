import { ImageComposeWorkspace } from "../components/ImageComposeWorkspace";

export default function ImageComposePage() {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(45,212,191,0.08),_transparent_55%),#050508] text-white">
      <div className="mx-auto w-full max-w-[1600px] px-6 pb-24 pt-12 md:px-12">
        <ImageComposeWorkspace />
      </div>
    </div>
  );
}
