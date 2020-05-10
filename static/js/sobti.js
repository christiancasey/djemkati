
function iris(m) {
  fPurple = 2*Math.PI/3.0;
  fScale = 0.8;
  fOffset = 0.0;
  vCM = new Array(m).fill(Array(3).fill(0));
  
  for(i=0;i<m;i++) {
    fTh = (i/m) * (Math.PI*2 - fPurple)
    vCM[i] = [ 
      Math.round(255 * (fScale*(Math.cos(fTh)+1)/2+fOffset)), 
      Math.round(255 * (fScale*(Math.cos(fTh-2*Math.PI/3)+1)/2+fOffset)), 
      Math.round(255 * (fScale*(Math.cos(fTh-4*Math.PI/3)+1)/2+fOffset))
    ];
  }
  return vCM;
}

