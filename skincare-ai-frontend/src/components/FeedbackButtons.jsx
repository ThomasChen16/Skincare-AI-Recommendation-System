// Feedback buttons component for product feedback
import { useState } from 'react'

function FeedbackButtons({ product, routineTime, user, currentFeedback, onFeedback, counts }) {
  // local state to track user's feedback
  const [localFeedback, setLocalFeedback] = useState(null)
  
  const handleFeedback = (rating) => {
    if (!user || !user.unique_id) {
      console.error("No user profile found. Cannot submit feedback.")
      return
    }
    
    // Optimistically update local state
    setLocalFeedback(rating)
    
    // send feedback to api
    onFeedback(product, rating, routineTime)
  }

  // determine which feedback to display
  const activeFeedback = localFeedback || currentFeedback

  return (
    <div className="feedback-buttons">
      <button
        onClick={() => handleFeedback('up')}
        className={`feedback-btn upvote ${activeFeedback === 'up' ? 'active' : ''}`}
        title="Good recommendation"
      >
        👍 <span className="feedback-count">{counts?.upvotes ?? 0}</span>
      </button>
      <button
        onClick={() => handleFeedback('down')}
        className={`feedback-btn downvote ${activeFeedback === 'down' ? 'active' : ''}`}
        title="Not a good recommendation"
      >
        👎 <span className="feedback-count">{counts?.downvotes ?? 0}</span>
      </button>
    </div>
  )
}

export default FeedbackButtons