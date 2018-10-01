const fs = require('fs')

function patch(txt, diff) {
  var lines = txt.split("\n"),
      difflines = diff.split("\n"),
      mode = null, remain = 0, diffat = 0, delta = 0, match
  for (var i = 0; i < difflines.length; i++) {
    var line = difflines[i]
    if ((match = /^([ad])(\d+) (\d+)/.exec(line)) != null) {
      mode = match[1]
      diffat = Number(match[2]) + delta
      remain = Number(match[3])
      // console.log([mode, diffat, remain])
      if (mode == "d") {
        diffat--
        lines.splice(diffat, remain)
        delta -= remain
      } else if (mode == "a") {
        // console.log(difflines.slice(i + 1, remain + i + 1).join("\n"))
        lines.splice(diffat, 0, ...difflines.slice(i + 1, remain + i + 1))
        delta += remain
        i += remain
      }
    }
  }
  return lines.join("\n")
}

var snap = fs.readFileSync('snap.html', 'utf-8')
var snapdiff = fs.readFileSync('snap.html.diff', 'utf-8')
console.log(patch(snap, snapdiff))
