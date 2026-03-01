import { useState, useRef } from 'react';
import './FileUpload.css';

export default function FileUpload({ onUploadComplete, isUploading }) {
    const [dragActive, setDragActive] = useState(false);
    const [file, setFile] = useState(null);
    const inputRef = useRef(null);

    const handleDrag = function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const processFile = async (uploadedFile) => {
        if (!uploadedFile) return;
        setFile(uploadedFile);
        await onUploadComplete(uploadedFile);
    };

    const handleDrop = function (e) {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            processFile(e.dataTransfer.files[0]);
        }
    };

    const handleChange = function (e) {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            processFile(e.target.files[0]);
        }
    };

    const handleButtonClick = () => {
        inputRef.current.click();
    };

    if (isUploading) {
        return (
            <div className="glass-panel loader-container animate-fade-in">
                <div className="spinner"></div>
                <h3 className="text-gradient">Analysing Financial Behaviour</h3>
                <p className="text-secondary" style={{ marginTop: '0.5rem' }}>
                    Extracting transactions, detecting patterns, and scoring risk...
                </p>
            </div>
        );
    }

    return (
        <form className="glass-panel animate-fade-in" onDragEnter={handleDrag} onSubmit={(e) => e.preventDefault()}>
            <input ref={inputRef} type="file" onChange={handleChange} accept=".csv,.xlsx,.tsv" style={{ display: 'none' }} />
            <div
                className={`drop-zone ${dragActive ? "drag-active" : ""}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                <div className="upload-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="17 8 12 3 7 8"></polyline>
                        <line x1="12" y1="3" x2="12" y2="15"></line>
                    </svg>
                </div>
                <h3>Drag and drop your bank statement</h3>
                <p className="upload-hint">Supports CSV, TSV, or XLSX. We automatically detect your bank format.</p>

                <button type="button" className="btn-primary" onClick={handleButtonClick}>
                    Select File
                </button>
            </div>
        </form>
    );
}
