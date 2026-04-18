import { useRef } from 'react';
import { QRCodeCanvas } from 'qrcode.react';
import { HiArrowDownTray } from 'react-icons/hi2';

export default function QRView() {
  const canvasRef = useRef(null);

  const shareData = JSON.stringify({
    app: 'Cognitive Health Twin',
    version: '0.1.0',
    user: 'demo-user',
    link: 'https://cognitive-twin.app/share/demo-user',
  });

  const handleDownload = () => {
    const canvas = canvasRef.current?.querySelector('canvas');
    if (canvas) {
      const link = document.createElement('a');
      link.download = 'cognitive-twin-qr.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    }
  };

  return (
    <div className="p-6 flex flex-col items-center justify-center h-full">
      <div className="text-center mb-6">
        <h2 className="text-xl font-semibold text-text-main">Share Your Twin</h2>
        <p className="text-sm text-text-muted mt-1">
          Scan this QR code to share your cognitive health profile with a care provider
        </p>
      </div>

      <div ref={canvasRef} className="p-6 rounded-xl border border-border bg-white inline-flex">
        <QRCodeCanvas
          value={shareData}
          size={200}
          fgColor="#202123"
          bgColor="#ffffff"
          level="H"
        />
      </div>

      <button
        onClick={handleDownload}
        className="mt-6 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:bg-primary-hover transition-colors cursor-pointer"
      >
        <HiArrowDownTray className="text-base" />
        Download QR Code
      </button>

      <p className="text-xs text-text-muted mt-4 text-center max-w-sm">
        Your shared data includes only summary insights. No raw health data is exposed.
      </p>
    </div>
  );
}
