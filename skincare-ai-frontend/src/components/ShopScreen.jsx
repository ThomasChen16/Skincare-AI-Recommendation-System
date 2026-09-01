// design for display real products for each of the recommended products in the routine
import { useState } from 'react'
import RealProductsList from './RealProductsList'

function ShopScreen({ amRoutine, pmRoutine, onNavigate }) {
    // one tab per unique recommended product - merge AM + PM and dedupe by product name
    const tabs = [...new Map([
        ...(amRoutine || []),
        ...(pmRoutine || [])
    ].map(p => [p.product, p])).values()]

    // track which tab is active. Store the product NAME (a stable key) so we always
    // know what to look up in the tabs array, regardless of array order or length.
    const [activeName, setActiveName] = useState(null)
    // Fall back to the first tab when nothing is selected yet (or the old selection is gone).
    // This also makes the first tab active on screen load with no extra effect needed.
    const activeProduct = tabs.find(t => t.product === activeName) ?? tabs[0]

    // if no routine yet, display a simple nothing here yet
    if (!tabs.length) {
        return (
            <div className='shop-screen'>
                <div className='shop-empty'>
                    <h2>Shop</h2>
                    <p>Nothing to show here yet.</p>
                    <p>Personalized products for your routine will appear once you generate one.</p>
                    <button onClick={() => onNavigate('routine')}>Build my routine</button>
                </div>
            </div>
        )
    }

    // return if there is a routine
    return (
        <div className='shop-screen'>
            <h2>Shop</h2>

            {/* one tab per recommended product - rendered dynamically from the routine */}
            <div className="shop-tabs">
                {tabs.map((product) => {
                    const isActive = product.product === activeProduct?.product
                    return (
                        <button key={product.product} className={`shop-tab${isActive ? ' active' : ''}`}
                                onClick={() => setActiveName(product.product)}>
                            {product.type}
                        </button>
                    )
                })}
            </div>

            {/* the currently-selected product and its real matches - reuse RealProductsList as-is */}
            <div className="shop-tab-content">
                <h3>{activeProduct.product}</h3>
                <p><strong>Type:</strong> {activeProduct.type}</p>
                <p><strong>Why this product:</strong> {activeProduct.reason}</p>
                <RealProductsList key={activeProduct.product} product={activeProduct} />
            </div>
        </div>
    )
}

export default ShopScreen