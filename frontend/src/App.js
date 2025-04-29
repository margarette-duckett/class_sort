import { useState, useRef, useEffect } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState({ started: false, pc: 0 });
  const [msg, setMsg] = useState(null);
  const [num_classes, setNumClasses] = useState(""); 
  const [downloadLink, setDownloadLink] = useState(null); 
  const downloadButtonRef = useRef(null);
  // Handle file selection
  function handleFileChange(event) {
    setFile(event.target.files[0]);
  }

  // Handle the number of classes input (set as an integer)
  function handleClassesChange(event) {
    const value = parseInt(event.target.value, 10); 
    setNumClasses(value);  
  }

  // Handle the file upload and sorting
  function handleUpload() {
    if (!file || num_classes <= 0 || isNaN(num_classes)) {
      setMsg("Please specify a valid number of classes and select a file.");
      return;
    }

    const fd = new FormData();
    fd.append("num_classes", num_classes);
    fd.append("file", file);
    
    setMsg("Uploading and Sorting ...");
    setProgress({ started: true, pc: 0 });

    axios
      .post('http://localhost:8000/process/', fd, {
        responseType: 'json', 
        onUploadProgress: (progressEvent) => {
          setProgress((prevState) => {
            return {
              ...prevState,
              pc: (progressEvent.loaded / progressEvent.total) * 100,
            };
          });
        },
      })
      .then((res) => {
        setMsg("Sorting Complete!");

        // Set the download link to be displayed as a button
        if (res.data && res.data.download_url) {
          setDownloadLink(res.data.download_url);
        } else {
          setMsg("Error: No download link provided.");
        }

      })
  
      .catch((err) => {
        setMsg("Upload failed");
        console.error(err);
      });
  }

  function handleMap() {
    const fd = new FormData();
    fd.append("file", file);
    
    setMsg("Calculating MAP scores ...");
    setProgress({ started: true, pc: 0 });

    axios
    .post("http://localhost:8000/calculate/", fd, {
      responseType: "json",
      onUploadProgress: (progressEvent) => {
        setProgress({
          started: true,
          pc: (progressEvent.loaded / progressEvent.total) * 100,
        });
      },
    })
    .then((res) => {
      if (res.data && res.data.download_url) {
        setDownloadLink(res.data.download_url); 
        setMsg("MAP_scores added");
      } else {
        setMsg("Error: No download link provided.");
      }
    })
    .catch((err) => {
      setMsg("MAP calculation failed. Please try again.");
      console.error(err);
    });
  }


  useEffect(() => {
    if (downloadButtonRef.current) {
      downloadButtonRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center', // Optional: align to center of viewport
      });
    }
  }, [downloadLink]);

  return (
    <div className="App">
      {/* Banner/Header */}
      <div className="banner" style={{ backgroundColor: "#0b2055" }}>
        <h2>ClassCraft</h2>
      </div>

      {/* Instructions */}
      <div className="text-container">
        <h2> File format requirments </h2>
        <p> To get started please follow these steps:</p>

        <ol>
          <li style={{ marginBottom: '10px' }}><strong>File Fortmatting</strong> : The file must be in CSV format. This means the file should either be created in programs like:
            <ul>
              <li><strong>Microsoft Excel</strong> (you can save this as a .csv from Excel)</li>
              <li><strong>Google Sheets</strong> (you can download this as a .csv)</li>
              <li>Or any simular spreadsheet tool that can save the file as a .csv</li>
            </ul>
          </li>
          <li style={{ marginBottom: '10px' }}><strong>File Contents</strong> : The file must contian atleast the following headers: 
            
              <ul><strong>ESOL</strong>: 
                <li>If the student is classifed ESOL, enter their first language.</li>
                <li>If the child is not ESOL leave the cell blank.</li> 
              </ul>
              <ul><strong>IEP</strong>: 
                <li>If the student has an IEP, enter the accommodation (e.g., "Speech", "Special Education").</li>
                <li>If the student does not have an IEP, leave the cell blank.</li> 
              </ul>
              <ul><strong>GATES</strong>: 
                <li>This field is for identifying advanced students.</li>
                <li>If the student is advanced enter yes, if not leave the cell blank.</li> 
              </ul>
              <ul><strong>MAP_score</strong>: 
                <li>This should be the average of the Math and Reading scores for the student (entered as a whole number, e.g., 80). If needed, upload the data to calculate this score.</li>
                <li><strong>You must include columns named "math_score" and "reading_score" to use this tool.</strong></li>
                <div style={{ marginTop: "10px" }}>
                <label>
                  Select a file to upload:
                  <input
                    type="file"
                    onChange={handleFileChange}
                    accept=".csv"
                  />
                </label>
              </div> 

              {/* Upload button */}
              <button style={{ marginBottom :"10px"}} onClick={handleMap}>Upload</button>
              {/* Show progress bar if upload started */}
              {progress.started && (
                <div>
                  <progress max="100" value={progress.pc}></progress>
                  <span>{Math.round(progress.pc)}%</span>
                </div>
              )}

              {/* Display message */}
              {msg && <span>{msg}</span>}

              {/* Display download button once sorting is complete */}
              {downloadLink && msg === "MAP_scores added" && (
                <div ref={downloadButtonRef}>
                  <h2>Addition complete</h2>
                  <a href={downloadLink} download>
                    <button>Download Updated File</button>
                  </a>
                </div>
              )}

              <li>Should you utilize this tool a new file will be given to you that includes the MAP_score. Use this new file in the next steps.</li>
              </ul>
            
          </li>
          
          <li style={{ marginBottom: '10px' }}><strong>Additional Headers</strong> :
            <ul>
              <li>You may include other columns (headers) for extra information (e.g., "Behavior_Tier")</li>
              <li><strong>The required headers must always be included.</strong></li>
            </ul>
          </li>
          
          <li style={{ marginBottom: '10px' }}><strong>Important Notes</strong>: 
            <ul>
              <li>Don't forget to save your file as a CSV. If you're using Excel or Google Sheets, make sure to select "CSV" as the file type when saving.</li>
              <li>Keep the header names exactly as shown to avoid errors. The system expects these specific names for processing.</li>
              <li style={{ color: "red" }}>The project does not replace professional educational tools or systems designed for comprehensive student data management. It should only be used as a reference or learning aid.</li>
              <li style={{ color: "red" }}>The sorting methods implemented in this project are based on standard algorithms and may not cover all edge cases or specific needs of educational institutions. The user assumes full responsibility for verifying the accuracy of the results when applying the project to real-world applications.</li>
            </ul>
          </li>
          
          <li style={{ marginBottom: '10px' }}><strong>File Snipet</strong> : The following is an example of a working CSV file.</li>
            <div className="csv-example">
            <img 
            src="/frontend_example.png" 
            alt="Example CSV"
            style={{width: '75%', height: 'auto'}} />
            </div>

        </ol>

      </div>

      {/* Step 1: Input for number of classes */}
      <div>
        <label>
          How many classes are available for students? (Enter an integer)
          <input
            type="text"
            placeholder="Enter number of classes"
            onChange={handleClassesChange}
            value={num_classes}
          />
        </label>
      </div>

      {/* Step 2: File upload input */}
      <div style={{ marginTop: "20px" }}>
        <label>
          Select a file to upload:
          <input
            type="file"
            onChange={handleFileChange}
            accept=".csv"
          />
        </label>
      </div>

      <br />

      {/* Upload button */}
      <button style={{ marginBottom :"10px"}} onClick={handleUpload}>Upload and Sort</button>

      {/* Show progress bar if upload started */}
      {progress.started && (
        <div>
          <progress max="100" value={progress.pc}></progress>
          <span>{Math.round(progress.pc)}%</span>
        </div>
      )}

      {/* Display message */}
      {msg && <span>{msg}</span>}

      {/* Display download button once sorting is complete */}
      {downloadLink && msg === "Sorting Complete!" && (
        <div ref={downloadButtonRef}>
          <h2>Sorting Complete!</h2>
          <a href={downloadLink} download>
            <button>Download Sorted Data</button>
          </a>
        </div>
      )}
    </div>
  );
}

export default App;
