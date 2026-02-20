  import React, { useState } from 'react';
  import axios from 'axios';
  import { FlaskConical, Map, CheckCircle } from 'lucide-react';
  import ReactMarkdown from 'react-markdown';
  import '../styles/recommend.css'; 

  // Crop data with direct image links
  const CROP_OPTIONS = [
    { name: "Maize", img: "https://img.icons8.com/color/96/corn.png" },
    { name: "Chilli", img: "https://img.icons8.com/color/96/chili-pepper.png" },
    { name: "Rice", img: "https://img.icons8.com/?size=100&id=fBRb__tw4Lft&format=png&color=000000" },
    { name: "Wheat", img: "https://img.icons8.com/color/96/wheat.png" },
    { name: "Cotton", img: "https://img.icons8.com/?size=100&id=YKUKiMCIwdhQ&format=png&color=000000" },
    { name: "Groundnut", img: "https://img.icons8.com/color/96/peanuts.png" },
    { name: "Tomato", img: "https://img.icons8.com/color/96/tomato.png" }
  ];

  export default function Recommend() {
    const [inputs, setInputs] = useState({ chemical: '', crop: '', acres: 1 });
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSearch = async () => {
      if (!inputs.chemical || !inputs.crop) {
        alert("Please enter a chemical and select a crop card.");
        return;
      }
      setLoading(true);
      try {
        const response = await axios.post('http://localhost:10000/recommend', inputs);
        setData(response.data);

      } catch (err) {
       setData(null); 
        
        if (err.response && err.response.status === 400) {
            // Show the specific message from Python ("I couldn't find a match...")
            alert(err.response.data.message);
        } else {
            // Show this ONLY if the Python server is actually off
            alert("Error connecting to AI Backend. Ensure your Python server is running.");
        }
      }
      setLoading(false);
    };

    return (
      <div className="recommend-viewport">
        <div className="recommend-container animate-fade-in">
          <header className="form-header">
            <h1>  <span className="organic-text">Organic</span> Recommendation </h1>
            <p>Sustainable Organic Alternatives for Your Farm</p>
          </header>

          <div className="glass-form-card">
            {/* Chemical Input */}
            <div className="input-group">
              <FlaskConical size={20} className="form-icon" />
              <input 
                placeholder="Chemical Name (e.g. Urea, DAP)" 
                value={inputs.chemical}
                onChange={(e) => setInputs({...inputs, chemical: e.target.value})} 
              />
            </div>

            {/* New Crop Card Selection */}
            <label className="section-label">Select Your Crop</label>
            <div className="crop-cards-grid">
              {CROP_OPTIONS.map((crop) => (
                <div 
                  key={crop.name}
                  className={`crop-card ${inputs.crop === crop.name ? 'active' : ''}`}
                  onClick={() => setInputs({ ...inputs, crop: crop.name })}
                >
                  <img src={crop.img} alt={crop.name} className="crop-icon-img" />
                  <span className="crop-name-label">{crop.name}</span>
                  {inputs.crop === crop.name && (
                    <CheckCircle size={18} className="selection-check" />
                  )}
                </div>
              ))}
            </div>

            {/* Acres Input */}
            <div className="input-group">
              <Map size={20} className="form-icon" />
              <input 
                type="number" 
                placeholder="Acres" 
                min="1"
                value={inputs.acres}
                onChange={(e) => setInputs({...inputs, acres: e.target.value})} 
              />
            </div>

            <button className="recommend-btn" onClick={handleSearch} disabled={loading}>
              {loading ? "AI is thinking..." : "Get Recommendation"}
            </button>
          </div>

          {data && (
            <div className="result-card animate-slide-up">
              <div className="result-header">
                <h2>Recommended: <span className="highlight-text">{data.alternative}</span></h2>
                <p> we recommend {data.alternative} over {inputs.chemical}</p>
              </div>
              <div className="result-grid">
                <div className="res-box"><strong>Dosage:</strong> {data.dosage}</div>
                <div className="res-box"><strong>Timing:</strong> {data.application_time}</div>
              </div>
              <div className="ai-advice-box">
                <h3>Expert AI Advice:</h3>
                <div className="advice-text">
                <ReactMarkdown>{data.llm_advice}</ReactMarkdown>
              </div>
              </div>
              <p className="safety-warning">⚠️ {data.safety_note}</p>
            </div>
          )}
        </div>
      </div>
    );
  }