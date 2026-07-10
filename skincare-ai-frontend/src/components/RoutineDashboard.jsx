// design for displaying routine with buttons for morning and night after finishing chat function
import { useState } from 'react'

function RoutineDashboard({ profile, onEditProfile }) {
    // routine will store the routine data returned and setRoutine is called to store the routine
    const [routine, setRoutine ] = useState(null) // useState(null) starts as null (no data yet)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [activeTime, setActiveTime] = useState(null) // 'a.m' or 'p.m' tracks which was last generated

    // when button is clicked
    async function generateRoutine(time) {
      // set loading to true displaying Generating your routine...
      setLoading(true)
      // clear previous error msg
      setError(null)
      // set to 'a.m' or 'p.m'
      setActiveTime(time)

      try {
        // fetch() browser fucntion that makes HTTP request
        const response = await fetch("http://localhost:8000/recommend", {
          method: "POST", // sending data to server
          headers: { 'Content-Type': 'application/json' }, // tell server we're sending JSON
          body: JSON.stringify({ // convert data to JSON string and send it to request body
            time: time,
            skin_type: profile.skin_type, // data saved in profile parameter which is analyzed variable
            concerns: profile.concerns,
            goals: profile.goals
          }),
        })

        // read the response body and converts the JSON to JavaScript object
        const data = await response.json()

        // call setRoutine adn store routine data
        setRoutine(data.routine)
      } catch (error) {
        setError("Something went wrong generating your routine. Please try again later.")
      } finally {
        setLoading(false)
      }
    }

  return (
    <div className="routine-dashboard">
      <div className="profile-summary">
        <h2>Your skin profile</h2>
        <p><strong>Skin Type:</strong> {profile.skin_type}</p>
        <p><strong>Concerns:</strong> {profile.concerns}</p>
        <p><strong>Goals:</strong> {profile.goals}</p>
      </div>

      <div className="routine-action">
        <button onClick={() => generateRoutine('a.m')}>Generate Morning Routine</button>
        <button onClick={() => generateRoutine('p.m')}>Generate Night Routine</button>
      </div>

      
      {loading && <p>Generating your routine...</p>}
      {error && <p>{error}</p>}

      {routine && routine.length > 0 && (
      <div className="routine-display">
          <h3>
              {activeTime === 'a.m' ? 'Morning' : 'Night'} Routine
          </h3>
          <ul className="routine-list">
            {routine.map((product, index) => (
              <li key={index} className="routine-item">
                <div className="step-number">Step {index + 1}</div>
                                  
                <div className="product-name">
                  <strong>Product:</strong> {product.product}
                </div>
                    
                <div className="product-type">
                  <strong>Type:</strong> {product.type}
                </div>
                    
                {product.reason && (
                  <div className="product-reason">
                    <strong>Why this product:</strong> {product.reason}
                  </div>
                )}
              </li>
              ))}
          </ul>
      </div>
      )}
    </div>
  )
}

export default RoutineDashboard