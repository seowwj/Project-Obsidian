import { useState } from 'react';
import { Upload, FileVideo, AlertCircle } from 'lucide-react';
import { open } from '@tauri-apps/plugin-dialog';
import { uploadVideo } from '../api/client';

interface VideoUploadProps {
    onUploadSuccess: (videoId: string) => void;
    onUploadError: (error: string) => void;
}

export function VideoUpload({ onUploadSuccess, onUploadError }: VideoUploadProps) {
    const [loading, setLoading] = useState(false);

    const handleUpload = async () => {
        try {
            const selected = await open({
                multiple: false,
                filters: [{
                    name: 'Video',
                    extensions: ['mp4', 'mkv', 'avi', 'mov']
                }]
            });

            if (selected && typeof selected === 'string') {
                const path = selected;
                setLoading(true);
                try {
                    // Pre-check limits (user feedback only, actual check in backend too)
                    // Note: Tauri dialog doesn't give file size directly without fs API,
                    // so we rely on backend for size error, but we show the limit in UI.

                    const vid = await uploadVideo(path);
                    onUploadSuccess(vid);
                } catch (err: any) {
                    console.error(err);
                    onUploadError(err.toString());
                } finally {
                    setLoading(false);
                }
            }
        } catch (err: any) {
            console.error(err);
            onUploadError("File selection failed: " + err.toString());
        }
    };

    return (
        <div className="flex flex-col items-center justify-center p-8 space-y-6 max-w-lg mx-auto w-full">
            <div className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full opacity-30 group-hover:opacity-75 transition duration-500 blur"></div>
                <div className="relative p-6 rounded-full bg-gray-800 border border-gray-700">
                    <FileVideo size={64} className="text-gray-400 group-hover:text-blue-400 transition-colors" />
                </div>
            </div>

            <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold text-gray-100">Upload Video</h2>
                <p className="text-gray-400 leading-relaxed">
                    Select a video to verify its content and start the analysis.
                </p>
            </div>

            <div className="w-full bg-gray-800/50 rounded-xl p-4 border border-gray-700/50 backdrop-blur-sm">
                <div className="flex items-start gap-3 text-sm text-gray-400">
                    <AlertCircle size={16} className="mt-0.5 text-blue-400 shrink-0" />
                    <div className="space-y-1">
                        <p className="font-medium text-gray-300">System Limits</p>
                        <ul className="list-disc pl-4 space-y-0.5">
                            <li>Max File Size: <span className="text-gray-200">200MB</span></li>
                            <li>Formats: <span className="text-gray-200">.mp4, .mkv, .mov, .avi</span></li>
                        </ul>
                    </div>
                </div>
            </div>

            <button
                onClick={handleUpload}
                disabled={loading}
                className="group relative flex items-center gap-2 px-8 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-full font-semibold text-white transition-all shadow-lg hover:shadow-blue-500/25 active:scale-95"
            >
                {loading ? (
                    <>Processing...</>
                ) : (
                    <>
                        <Upload size={18} />
                        <span>Select File</span>
                    </>
                )}
            </button>
        </div>
    );
}
