// design for displaying routine with buttons for morning and night after finishing chat function
import { useState, useEffect } from 'react'
import FeedbackButtons from './FeedbackButtons'

function RoutineDashboard({ profile, amRoutine, pmRoutine, onGenerateRoutine, routineLoading, routineError, onFeedback, onFetchCounts, feedbackMap, user }) {
    // local state for AM/PM routines
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [activeTime, setActiveTime] = useState(null) // 'a.m' or 'p.m' tracks which was last generated
    const [saved, setSaved] = useState(false) // track if routines were saved
    const [feedbackCounts, setFeedbackCounts] = useState({}) // track feedback counts for product
    
    // DEBUG: Log props
    console.log('RoutineDashboard props:', { profile, amRoutine, pmRoutine })
    
    // useEffect to show save status
    useEffect(() => {
      // check if routines were provided and have content
      console.log('Checking routines:', { amRoutine, pmRoutine, amLength: amRoutine?.length, pmLength: pmRoutine?.length }) // DEBUG
      if ((amRoutine && amRoutine.length > 0) || (pmRoutine && pmRoutine.length > 0)) {
        setSaved(true)
      }

      async function loadCounts() {
        // Collect the product names used to look up aggregate feedback counts.
        const productNames = [...(amRoutine || []), ...(pmRoutine || [])].map(item => item.product)
        if (productNames.length === 0 || !onFetchCounts) return
        // Fetch the counts and store them so the dashboard can display updated feedback data.
        const counts = await onFetchCounts(productNames)
        setFeedbackCounts(counts)
      }
      loadCounts()
    }, [amRoutine, pmRoutine])

    // Re-fetch counts after the user submits feedback so the displayed numbers update immediately.
    const handleFeedback = async (product, rating, routineTime) => {
      await onFeedback(product, rating, routineTime)
      if (onFetchCounts) {
        const productNames = [...(amRoutine || []), ...(pmRoutine || [])].map(item => item.product)
        const counts = await onFetchCounts(productNames)
        setFeedbackCounts(counts)
      }
    }


    // Javascript object
    return (
      <div className="routine-dashboard">
        {/* Photo banner */}
        <div className="routine-banner">
          <img src="/pictures/skincare-pic3.jpg" alt="Skincare products" />
          <div className="routine-banner-overlay">
            <span className="routine-banner-badge">Your Routine</span>
            <h2>Personalized for your skin</h2>
            <p>Curated products matched to your skin type, concerns and goals</p>
          </div>
        </div>

        <div className="profile-summary">
          <h2>Your skin profile</h2>
          {profile ? (
            <>
              <p><strong>Skin Type:</strong> {profile.skin_type}</p>
              <p><strong>Concerns:</strong> {profile.concerns?.join(', ') || 'None'}</p>
              <p><strong>Goals:</strong> {profile.goals?.join(', ') || 'None'}</p>
            </>
          ) : (
            <p>Loading profile...</p>
          )}
        </div>

        {saved && (
          <p className="saved-status">✓ Routine saved to your profile</p>
        )}

        {/* Show generate button if no routines exist */}
        {(!amRoutine || amRoutine.length === 0) && (!pmRoutine || pmRoutine.length === 0) && onGenerateRoutine && (
          <div>
            <button onClick={onGenerateRoutine} className="generate-routine-btn" disabled={routineLoading}>
              {routineLoading ? 'Generating… (first load can take ~20s)' : 'Generate My Skincare Routine'}
            </button>
            {routineError && <p className="routine-error">⚠️ {routineError}</p>}
          </div>
        )}

        {(amRoutine && amRoutine.length > 0) || (pmRoutine && pmRoutine.length > 0) ? (
          <div className="routines-container">
            {amRoutine && amRoutine.length > 0 && (
              <div className="routine-section">
                <h3>Morning Routine</h3>
                <div className="routine-list">
                  {amRoutine.map((product, index) => (
                    <div key={index} className="product-card">
                      <h4>{product.product}</h4>
                      <p><strong>Type:</strong> {product.type}</p>
                      <p><strong>Score:</strong> {product.score}</p>
                      <p><strong>Why this product:</strong> {product.reason}</p>
                      <FeedbackButtons
                        product={product}
                        routineTime="am"
                        user={user}
                        currentFeedback={feedbackMap[product.product]}
                        onFeedback={handleFeedback}
                        counts={feedbackCounts[product.product]}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {pmRoutine && pmRoutine.length > 0 && (
              <div className="routine-section">
                <h3>Evening Routine</h3>
                <div className="routine-list">
                  {pmRoutine.map((product, index) => (
                    <div key={index} className="product-card">
                      <h4>{product.product}</h4>
                      <p><strong>Type:</strong> {product.type}</p>
                      <p><strong>Score:</strong> {product.score}</p>
                      <p><strong>Why this product:</strong> {product.reason}</p>
                      <FeedbackButtons
                        product={product}
                        routineTime="pm"
                        user={user}
                        currentFeedback={feedbackMap[product.product]}
                        onFeedback={handleFeedback}
                        counts={feedbackCounts[product.product]}
                      />
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