const cache = {};

function renderMathDeffered(elementId) {
    const {MathJax} = window;
    if (MathJax) {
        const el = document.getElementById(elementId);
        if (el) {
            const key = elementId;
            if (cache.hasOwnProperty(key)) {
                el.outerHTML = cache[key].outerHTML;
                return
            }

            MathJax.Hub.queue.Push(["Typeset", MathJax.Hub, elementId], () => {
                const el = document.getElementById(elementId);
                if (el) {
                    el.style.visibility = "visible";
                    cache[key] = el;
                }
            });
        }
    }
}

function renderMath(elementId) {
    setTimeout(() => {
        renderMathDeffered(elementId)
    }, 0);
}

export {renderMath};