export const areSetsEqual = (a, b) => a.size === b.size && [...a].every(value => b.has(value));

export function calculateHash(value) {
    let hash = 0, i, chr;
    for (i = 0; i < value.length; i++) {
        chr   = value.charCodeAt(i);
        hash  = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash - (1 << 31);
}