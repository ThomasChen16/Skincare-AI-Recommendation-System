// Display real products in a catalog card screen
import { useState } from 'react'

// receive the product it would show real products for
function RealProductsList({ product }) {
    const realProducts = product?.real_products || [] // pull the data off the product
    const [expanded, setExpanded] = useState(false) // local expand/collapse state for displaying real products

    // if no real products don't render anything
    if (realProducts.length === 0) return null

    // collapsed -> only the top 3, as individual cards
    // expanded  -> ALL products in one scrollable box, each with its ingredients
    const visible = expanded ? realProducts : realProducts.slice(0, 3)

    return (
        <div className='real_products'>
            <div className='rp-heading'>
                <h5>Real products you can buy</h5>
                <span className='rp-count'>{realProducts.length} matches</span>
            </div>

            <div className={`rp-list${expanded ? ' rp-list-expanded' : ''}`}>
                {visible.map((rp, i) => (
                    <div key={i} className='real-product-card'>
                        <div className='rp-card-top'>
                            <div className='rp-title-block'>
                                {rp.brand && <span className='rp-brand'>{rp.brand}</span>}
                                {rp.url ? (
                                    <a className='rp-name' href={rp.url} target="_blank" rel="noreferrer">
                                        {rp.product}
                                        <span className='rp-ext' aria-hidden="true">↗</span>
                                    </a>
                                ) : (
                                    <span className='rp-name'>{rp.product}</span>
                                )}
                            </div>
                            {rp.price && <span className='rp-price'>{rp.price}</span>}
                        </div>

                        <div className='rp-meta'>
                            {i === 0 && <span className='rp-chip rp-chip-top'>Top match</span>}
                            {rp.category && <span className='rp-chip'>{rp.category}</span>}
                        </div>

                        {rp.ingredients && (
                            <div className='rp-ingredients-block'>
                                <span className='rp-ingredients-label'>Ingredients</span>
                                <p className='rp-ingredients'>{rp.ingredients}</p>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {realProducts.length > 3 && (
                <button className='rp-toggle-btn' onClick={() => setExpanded(prev => !prev)}>
                    {expanded ? 'Show less' : `Show all ${realProducts.length} matches`}
                </button>
            )}
        </div>
    )
}

export default RealProductsList