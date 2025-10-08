import { ChangeEvent, FormEvent, PointerEvent, useEffect, useMemo, useRef, useState } from "react";

const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15 MB
const TRAIL_LENGTH = 6;
const TRAIL_SIZES = [320, 280, 240, 200, 160, 140];
const TRAIL_COLORS = [
  "rgba(99, 102, 241, 0.65)",
  "rgba(56, 189, 248, 0.5)",
  "rgba(236, 72, 153, 0.45)",
  "rgba(129, 140, 248, 0.4)",
  "rgba(14, 165, 233, 0.35)",
  "rgba(217, 70, 239, 0.32)",
];

type UploadState = "idle" | "uploading" | "success" | "error";

interface UploadError {
  message: string;
  details?: string;
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadState>("idle");
  const [error, setError] = useState<UploadError | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const pageRef = useRef<HTMLDivElement>(null);
  const trailTargetRef = useRef({ x: 0, y: 0, active: false });
  const animationRef = useRef<number>();
  const [trail, setTrail] = useState(() =>
    Array.from({ length: TRAIL_LENGTH }, () => ({ x: 0, y: 0, opacity: 0 }))
  );

  useEffect(() => {
    if (!pageRef.current) return;
    const rect = pageRef.current.getBoundingClientRect();
    trailTargetRef.current.x = rect.width / 2;
    trailTargetRef.current.y = rect.height / 2;
  }, []);

  useEffect(() => {
    const animate = () => {
      setTrail(prev => {
        const next = [...prev];
        let leadX = trailTargetRef.current.x;
        let leadY = trailTargetRef.current.y;

        for (let index = 0; index < TRAIL_LENGTH; index++) {
          const point = prev[index];
          const ease = index === 0 ? 0.2 : 0.24;
          const x = point.x + (leadX - point.x) * ease;
          const y = point.y + (leadY - point.y) * ease;
          const opacityTarget = trailTargetRef.current.active ? Math.max(0, 0.85 - index * 0.13) : 0;
          const opacity = point.opacity + (opacityTarget - point.opacity) * 0.18;

          next[index] = { x, y, opacity };
          leadX = x;
          leadY = y;
        }

        return next;
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  const fileHint = useMemo(() => {
    if (!selectedFile) return "";
    return `${selectedFile.name} (${formatBytes(selectedFile.size)})`;
  }, [selectedFile]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setSuccessMessage(null);
    const file = event.target.files?.[0];
    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith(".xml") && !file.name.toLowerCase().endsWith(".xbrl")) {
      setError({ message: "Only .xml or .xbrl files are supported." });
      event.target.value = "";
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError({ message: `File exceeds the ${formatBytes(MAX_FILE_SIZE)} limit.` });
      event.target.value = "";
      return;
    }

    setSelectedFile(file);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!selectedFile) {
      setError({ message: "Please choose an XBRL file before uploading." });
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setState("uploading");
    try {
      const response = await fetch("/api/v1/files/xbrl-to-excel", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let message = `Failed to convert XBRL file (status ${response.status})`;
        const contentType = response.headers.get("content-type") ?? "";
        try {
          if (contentType.includes("application/json")) {
            const payload = await response.json();
            if (typeof payload === "string" && payload.trim()) {
              message = payload.trim();
            } else if (payload?.detail) {
              if (typeof payload.detail === "string") {
                message = payload.detail;
              } else {
                message = JSON.stringify(payload.detail);
              }
            }
          } else {
            const text = (await response.text()).trim();
            if (text) {
              message = text;
            }
          }
        } catch (parseError) {
          console.warn("Failed to parse error response", parseError);
        }
        throw new Error(message);
      }

      const blob = await response.blob();
      const filename = response.headers.get("Content-Disposition")?.split("filename=")[1]?.replace(/"/g, "");
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename || `xbrl-export-${Date.now()}.xlsx`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      setSuccessMessage("Excel workbook downloaded successfully.");
      setState("success");
    } catch (uploadError) {
      console.error(uploadError);
      const message = uploadError instanceof Error ? uploadError.message : "Unexpected error occurred.";
      setError({ message });
      setState("error");
    }
  };

  const handlePointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (!pageRef.current) return;
    const rect = pageRef.current.getBoundingClientRect();
    trailTargetRef.current.x = event.clientX - rect.left;
    trailTargetRef.current.y = event.clientY - rect.top;
    trailTargetRef.current.active = true;
  };

  const handlePointerLeave = () => {
    trailTargetRef.current.active = false;
  };

  const handlePointerDown = (event: PointerEvent<HTMLDivElement>) => {
    handlePointerMove(event);
  };

  return (
    <div
      ref={pageRef}
      className="page"
      onPointerMove={handlePointerMove}
      onPointerEnter={handlePointerMove}
      onPointerDown={handlePointerDown}
      onPointerLeave={handlePointerLeave}
    >
      <div className="cursor-trail" aria-hidden>
        {trail.map((point, index) => (
          <span
            key={index}
            className="cursor-trail__node"
            style={{
              top: `${point.y}px`,
              left: `${point.x}px`,
              opacity: point.opacity,
              width: `${TRAIL_SIZES[index]}px`,
              height: `${TRAIL_SIZES[index]}px`,
              background: `radial-gradient(circle at center, ${TRAIL_COLORS[index]} 0%, rgba(2, 6, 23, 0) 70%)`,
              filter: `blur(${Math.max(30 - index * 3, 12)}px)`,
            }}
          />
        ))}
      </div>
      <div className="card">
        <div className="card__panel card__panel--narrative">
          <header className="card__header">
            <p className="card__eyebrow">Financial Data Gear</p>
            <h1>
              <span className="card__title-accent">Convert your </span>XBRL to Excel
            </h1>
            <p>
              Drop your official MCA AOC-4 XBRL filing and we’ll transform it into a clean Excel workbook with Ind AS mapping,
              validation notes, and an export-ready audit trail.
            </p>
          </header>

          <div className="card__stats">
            <div className="card__stat">
              <span className="card__stat-value">97%</span>
              <span className="card__stat-label">Ind AS taxonomy coverage</span>
            </div>
            <div className="card__stat">
              <span className="card__stat-value">60s</span>
              <span className="card__stat-label">Average conversion time</span>
            </div>
            <div className="card__stat">
              <span className="card__stat-value">0</span>
              <span className="card__stat-label">Files stored after export</span>
            </div>
          </div>

          <section className="info info--feature">
            <h2>What you get</h2>
            <ul className="info__grid">
              <li>
                <span className="info__label">Automated mapping</span>
                <span className="info__copy">We resolve Ind AS concepts, contexts, and units so each figure lands on the right sheet.</span>
              </li>
              <li>
                <span className="info__label">Built-in validation</span>
                <span className="info__copy">Cross-checks important totals with configurable tolerances and surfaces potential misstatements.</span>
              </li>
              <li>
                <span className="info__label">Audit trail tabs</span>
                <span className="info__copy">Every number is traceable back to the original XBRL fact, including context IDs and source hyperlinks.</span>
              </li>
            </ul>
          </section>

          <section className="info info--secondary">
            <h2>How it works</h2>
            <ol className="info__steps">
              <li>
                <strong>Upload</strong> your `.xml` or `.xbrl` filing exported from MCA.
              </li>
              <li>
                <strong>Parse &amp; validate.</strong> We crunch the taxonomy, apply Ind AS mappings, and flag any anomalies.
              </li>
              <li>
                <strong>Download</strong> the Excel workbook with statement tabs, control checks, and the audit trail.
              </li>
            </ol>
            <p className="info__footnote">Designed for finance, audit, and analytics teams who need shareable data without hand-copying figures.</p>
          </section>
        </div>

        <div className="card__panel card__panel--form">
          <div className="panel__intro">
            <h2>Upload &amp; convert</h2>
            <p>Choose your XBRL file to generate a downloadable Excel workbook with one click.</p>
          </div>

          <form className="upload-form" onSubmit={handleSubmit}>
            <div className="upload-form__picker">
              <label htmlFor="file">
                <span className="picker__headline">Click to choose a file</span>
                <span className="picker__hint">Supported formats: .xml, .xbrl • Max size {formatBytes(MAX_FILE_SIZE)}</span>
                <input
                  id="file"
                  name="file"
                  type="file"
                  accept=".xml,.xbrl"
                  onChange={handleFileChange}
                  disabled={state === "uploading"}
                />
              </label>
              {fileHint && <p className="picker__selection">Selected: {fileHint}</p>}
            </div>

            {error && (
              <div className="alert alert--error">
                <strong>Error:</strong> {error.message}
              </div>
            )}

            {successMessage && <div className="alert alert--success">{successMessage}</div>}

            <button type="submit" className="cta" disabled={state === "uploading"}>
              {state === "uploading" ? "Processing…" : "Generate Excel"}
            </button>
          </form>

          <div className="panel__footnote">
            <p>Conversion runs in-memory. No data is persisted once your workbook is delivered.</p>
            <p className="panel__help-text">Need help? Drop me a note at <span>palprakashpraveen@gmail.com</span>.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
