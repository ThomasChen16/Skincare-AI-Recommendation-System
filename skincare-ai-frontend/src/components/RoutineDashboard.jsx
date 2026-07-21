// design for displaying routine with buttons for morning and night after finishing chat function
import { useState, useEffect } from 'react'

function RoutineDashboard({ profile, onEditProfile, amRoutine, pmRoutine, onGenerateRoutine }) {
    // local state for AM/PM routines
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [activeTime, setActiveTime] = useState(null) // 'a.m' or 'p.m' tracks which was last generated
    const [saved, setSaved] = useState(false) // track if routines were saved
    
    // DEBUG: Log props
    console.log('RoutineDashboard props:', { profile, amRoutine, pmRoutine })
    
    // useEffect to show save status
    useEffect(() => {
      // check if routines were provided and have content
      console.log('Checking routines:', { amRoutine, pmRoutine, amLength: amRoutine?.length, pmLength: pmRoutine?.length }) // DEBUG
      if ((amRoutine && amRoutine.length > 0) || (pmRoutine && pmRoutine.length > 0)) {
        setSaved(true)
      }
    }, [amRoutine, pmRoutine])

    // Javascript object
    return (
      <div className="routine-dashboard">
          <div className="profile-summary">
              <h2>Your skin profile</h2>
              <p><strong>Skin Type:</strong> {profile.skin_type}</p>
              <p><strong>Concerns:</strong> {profile.concerns.join(', ')}</p>
              <p><strong>Goals:</strong> {profile.goals.join(', ')}</p>
              <button onClick={onEditProfile}>Edit Profile</button>
          </div>

      {saved && (
        <p className='saved-status'>✓ Routine saved to your profile</p>
      )}

      {/* Show generate button if no routines exist */}
      {(!amRoutine || amRoutine.length === 0) && (!pmRoutine || pmRoutine.length === 0) && onGenerateRoutine && (
        <button onClick={onGenerateRoutine} className='generate-routine-btn'>
          Generate My Skincare Routine
        </button>
      )}

      {(amRoutine && amRoutine.length > 0) || (pmRoutine && pmRoutine.length > 0) ? (
        <div className='routines-container'>
          {amRoutine && amRoutine.length > 0 && (
            <div className='routine-section'>
              <h3>Morning Routine (AM)</h3>
              <div className='routine-list'>
                {amRoutine.map((product, index) => (
                  <div key={index} className='product-card'>
                    <h4>{product.product}</h4>
                    <p>Type: {product.type}</p>
                    <p>Score: {product.score}</p>
                    <p>Why this product: {product.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {pmRoutine && pmRoutine.length > 0 && (
            <div className='routine-section'>
              <h3>Evening Routine (PM)</h3>
              <div className='routine-list'>
                {pmRoutine.map((product, index) => (
                  <div key={index} className='product-card'>
                    <h4>{product.product}</h4>
                    <p>Type: {product.type}</p>
                    <p>Score: {product.score}</p>
                    <p>Why this product: {product.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
    )
}

export default RoutineDashboard