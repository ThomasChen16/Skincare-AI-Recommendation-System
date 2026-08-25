// Display real products in a catalog card screen
import { useState } from 'react'

// receive the product it would show real products for
function RealProductsList({ product }) {
    const realProducts = product?.real_products || [] // pull the data off the product
    const [expanded, setExpanded] = useState(false) // local expand/collapse state for displaying real products

    // if no real products don't render anything
    if (realProducts.length === 0) return null

    // decide which items to show:
    //   collapsed -> only the top 3, as individual cards
    //   expanded  -> ALL products in one scrollable box (replaces the top 3)
    const visible = expanded ? realProducts : realProducts.slice(0, 3)

    return (
        <div className='real_products'>
            <h5>Real products you can buy</h5>
            {expanded ? (
                <div className="rp-more-scroll">
                    {visible.map((rp, i) => (
                        <div key={i} className='real-product-card'>
                            <a href={rp.url} target="_blank" rel="noreferrer">{rp.product}</a>
                            <span> · {rp.category} · {rp.price}</span>
                            <p className="rp-reason">{rp.reason}</p>
                            <p className="rp-ingredients">{rp.ingredients}</p>
                        </div>
                    ))}
                </div>
            ) : (
                visible.map((rp, i) => (
                    <div key={i} className='real-product-card'>
                        <a href={rp.url} target="_blank" rel="noreferrer">{rp.product}</a>
                        <span> · {rp.category} · {rp.price}</span>
                        <p className="rp-reason">{rp.reason}</p>
                    </div>
                ))
            )}
            {realProducts.length > 3 && (
                <button onClick={() => setExpanded(prev => !prev)}>
                    {expanded ? 'See less' : `See more (${realProducts.length - 3})`}
                </button>
            )}
        </div>
    )
 }

 export default RealProductsList
