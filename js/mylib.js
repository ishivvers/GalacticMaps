// js library for SN history page

function arraysEqual(a, b) {
  if (a === b) {return true;}
  if (a == null || b == null) {return false;}
  if (a.length != b.length) {return false;}
  for (var i = 0; i < a.length; ++i) {
    if (a[i] !== b[i]) {return false;}
  }
  return true;
}

function index_of(a, obj) {
    var i = a.length;
    while (i--) {
       if (arraysEqual(a[i],obj)) {
           return i;
       }
    }
    return -1;
}

function gal2proj(l,b,proj) {
	// Convert galactic coordinates l,b into projected image positions
	if (l < 180.0) {
		var x = -l
	}
	else {
		var x = 180 - (l%180.0)
	}
	var y = b
	return proj([String(d3.round(x,5)), String(d3.round(y,5))])
}

var active_objs = new Array();
function explosion(l,b,value,index) {
	// requires a d3.geo projection in the namespace as 'projection'
	// and requires the svg to be called svg
	// value can be a size (for SN page) or
	// an array of time and size (for GRB page)
	var coords = gal2proj(l, b, projection);
	var c = svg.append('circle');
	if (active_objs.indexOf(index) !== -1) {
		c.attr("class", "activedot");
	}
	else {
		c.attr("class", "dot");
	}
	if (thispage == 'sne') {
		c.datum(index)
			.attr('cx', coords[0])
			.attr('cy', coords[1])
			.attr('r', 1)
			.on("click", function(d) {show_SN_info(d);})
			.transition()
			    .delay(100)
			    .duration(800)
			    .attr("r",value)
			.transition()
			    .duration(300)
			    .style("opacity",0)
			.remove();
	}
	else if (thispage == 'grbs') {
		var tGrow = d3.round(.9*value[0]);
		c.datum(index)
			.attr('cx', coords[0])
			.attr('cy', coords[1])
			.attr('r', 1)
			.on("click", function(d) {show_GRB_info(d);})
			.transition()
			    .delay(100)
			    .duration(tGrow)
			    .attr("r", value[1])
			.transition()
			    .duration(value[0]-tGrow)
			    .style("opacity",0)
			.remove();
	}
}

var currently_pulsing = new Array();
var nrings = 5;
function pulsar(i) {
	// append to the svg the pulsar corresponding to index i
	var coords = gal2proj(all_objs[i].coords[0], all_objs[i].coords[1], projection);
	var size = rScale3(Math.log(all_objs[i]['flux']));
	var time = tScale2(all_objs[i]['period']);
	if (active_objs.indexOf(i) == -1) {
		// the center dot
		svg.append('circle')
		   .datum(i)
           .attr("class", "dot")
		   .attr("r", 0.75*size)
		   .attr("cx",coords[0])
		   .attr("cy", coords[1])
			.on("click", function(d) {show_PLSR_info(d);});
		// the expanding waves
		svg.append("circle")
			.datum(i)
			.attr("class", "ring")
			.attr("r", 0.25*size)
			.attr("cx", coords[0])
			.attr("cy", coords[1])
			.attr("stroke-width", 2)
			.on("click", function(d) {show_PLSR_info(d);})
			.transition()
			    .delay(nrings*0.25*time)
				.duration(nrings*0.75*time)
				.style("stroke-opacity", 0.01)
				.attr("r", size)
			.remove();
		var intv = setInterval(function() {
			svg.append("circle")
				.datum(i)
				.attr("class", "ring")
				.attr("r", 0.25*size)
				.attr("cx", coords[0])
				.attr("cy", coords[1])
				.attr("stroke-width", 2)
			.on("click", function(d) {show_PLSR_info(d);})
			.transition()
			    .delay(nrings*0.25*time)
				.duration(nrings*0.75*time)
				.style("stroke-opacity", 0.01)
				.attr("r", size)
			.remove();
		}, time);
	}	
	else {
		svg.append('circle')
		   .datum(i)
           .attr("class", "activedot")
		   .attr("r", 0.75*size)
		   .attr("cx",coords[0])
		   .attr("cy", coords[1])
			.on("click", function(d) {show_PLSR_info(d);});
		svg.append("circle")
			.datum(i)
			.attr("class", "activering")
			.attr("r", 0.25*size)
			.attr("cx", coords[0])
			.attr("cy", coords[1])
			.attr("stroke-width", 2)
			.on("click", function(d) {show_PLSR_info(d);})
			.transition()
			    .delay(nrings*0.25*time)
				.duration(nrings*0.75*time)
				.style("stroke-opacity", 0.01)
				.attr("r", size)
			.remove();
		var intv = setInterval(function() {
			svg.append("circle")
				.datum(i)
				.attr("class", "activering")
				.attr("r", 0.25*size)
				.attr("cx", coords[0])
				.attr("cy", coords[1])
				.attr("stroke-width", 2)
				.on("click", function(d) {show_PLSR_info(d);})
				.transition()
				    .delay(nrings*0.25*time)
					.duration(nrings*0.75*time)
					.style("stroke-opacity", 0.01)
					.attr("r", size)
				.remove();
		}, time);
	}
	currently_pulsing.push(intv);
}


function show_SN_info(i) {
	var htmlstring = '<div class="row"><div class="span2" id="image"></div><div class="span3 offset1">';
	// insert the info for the SN into the template
	active_objs = [i];
	htmlstring += '<h1>'+all_objs[i].name+'</h1> <ul>';
	htmlstring += '<li>Right Ascension: '+String(d3.round(all_objs[i].eqcoords[0],2))+'&deg;</li>';
	htmlstring += '<li>Declination: '+String(d3.round(all_objs[i].eqcoords[1],2))+'&deg;</li>';
    if (all_objs[i].type) {
		htmlstring += '<li>Type: '+all_objs[i].type+'</li>';
	}
    if (all_objs[i].magnitude) {
		htmlstring += '<li>Magnitude: '+all_objs[i].magnitude+'</li>';
	}
	htmlstring += '<li>Discovery Date: '+all_objs[i].date+'</li>';
	if (all_objs[i].galaxy) {
		if (all_objs[i].galaxy == 'Anon.') {
			htmlstring += '<li>Host Galaxy: ' + all_objs[i].galaxy + '</li>';
		}
		else {
			htmlstring += '<li><a target="_blank" href="' +
						  'http://simbad.u-strasbg.fr/simbad/sim-id?Ident=' + all_objs[i].galaxy +
						  '&NbIdent=1&Radius=2&Radius.unit=arcmin">Host Galaxy: ' +
						  all_objs[i].galaxy+'</a></li>';
		}
	}
    if (all_objs[i].authors) {
		htmlstring += '<li>Identified by: '+all_objs[i].authors+'</li>';
	}
	htmlstring += '<li><a target="_blank" href="' + 
	              'http://simbad.u-strasbg.fr/simbad/sim-id?Ident=' + all_objs[i].name +
	              '&NbIdent=1&Radius=2&Radius.unit=arcmin">More info (if available)</a></li>';
    htmlstring += '</ul><br></div></div>';
    // now put into the visible page
    document.getElementById('main_txt').innerHTML = htmlstring;
	document.getElementById('main_txt').scrollIntoView();
	// and put in a callback to insert the image
	insert_image(i);
}

function show_GRB_info(i) {
	var htmlstring = '<div class="row"><div class="span2" id="image"></div><div class="span3 offset1">';
	// insert the info for the GRB into the template
	active_objs = [i];
	htmlstring += '<h1>GRB '+all_objs[i].name+'</h1> <ul>';
	htmlstring += '<li>Right Ascension: '+String(d3.round(all_objs[i].eqcoords[0],2))+'&deg;</li>';
	htmlstring += '<li>Declination: '+String(d3.round(all_objs[i].eqcoords[1],2))+'&deg;</li>';
	htmlstring += '<li>Discovery Date: '+all_objs[i].date+'</li>';
	htmlstring += '<li>Observatory: '+all_objs[i].observatory+'</li>'
	if ((all_objs[i].flag == 0) || (all_objs[i].flag == 1)) {
		htmlstring += '<li>Burst Length: '+String(all_objs[i].t90)+' seconds</li>'
	}
	htmlstring += '<li><a target="_blank" href="' + 
	              'http://simbad.u-strasbg.fr/simbad/sim-id?Ident=GRB+' + all_objs[i].name +
	              '&NbIdent=1&Radius=2&Radius.unit=arcmin">More info (if available)</a></li>';
    htmlstring += '</ul><br></div></div>';
    // now put into the visible page
    document.getElementById('main_txt').innerHTML = htmlstring;
	document.getElementById('main_txt').scrollIntoView();
	// and put in a callback to insert the image
	insert_image(i);
}

function show_PLSR_info(i) {
	var htmlstring = '<div class="row"><div class="span2" id="image"></div><div class="span3 offset1">';
	// insert the info for the pulsar into the template
	active_objs = [i];
	show_bin(all_objs[i].bin);
	htmlstring += '<h1>'+all_objs[i].name+'</h1> <ul>';
	htmlstring += '<li>Right Ascension: '+String(d3.round(all_objs[i].eqcoords[0],2))+'&deg;</li>';
	htmlstring += '<li>Declination: '+String(d3.round(all_objs[i].eqcoords[1],2))+'&deg;</li>';
	htmlstring += '<li>Discovery Year: '+all_objs[i].year+'</li>';
	htmlstring += '<li>Period: '+d3.round(all_objs[i].period,4)+' seconds</li>';
	htmlstring += '<li>Distance: '+d3.round(all_objs[i].distance)+' lightyears</li>';	
	htmlstring += '<li><a target="_blank" href="' + 
	              'http://simbad.u-strasbg.fr/simbad/sim-id?Ident=PSR+' + all_objs[i].name.replace('+','%2B') +
	              '&NbIdent=1&Radius=2&Radius.unit=arcmin">More info (if available)</a></li>';
	// htmlstring += '<li><a target="_blank" href="http://www.wolframalpha.com/input/?i=psr+' + 
	//               all_objs[i].name.replace('+','%2B') + '">More Info B</a></li>'  // doesn't work for all pulsars
    htmlstring += '</ul><br></div></div>';
    // now put into the visible page
    document.getElementById('main_txt').innerHTML = htmlstring;
	document.getElementById('main_txt').scrollIntoView();
	// and put in a callback to insert the image
	insert_image(i);
}

function insert_image(i) {
	// inserts an insert of the field with coordinates overlain
	var coords = all_objs[i].eqcoords
	var image_src = 'http://archive.stsci.edu/cgi-bin/dss_search?v=3&amp;r=' +
	                 String(coords[0]) + '&amp;d=' + String(coords[1]) + 
	'&amp;h=5.0&amp;w=5.0&amp;f=gif&amp;c=none&amp;fov=NONE&amp;e=J2000';
	var w = 200, h = 200;
	var svg2 = d3.select("#image").append("svg")
        .attr("height", h)
        .attr("width", w);
	svg2.append("image")
		.attr("xlink:href", image_src)
		.attr("width", w)
		.attr("height", h);
	// coordinate arrows (not very accurate)
	// svg2.append("svg:line")  //pointing up
	// 	.attr("class","pointer")
	// 	.attr("x1", w/2)
	// 	.attr("y1", (h/2)-10)
	// 	.attr("x2", w/2)
	// 	.attr("y2", (h/2)-50);
	// svg2.append("svg:line")  //pointing right
	// 	.attr("class","pointer")
	// 	.attr("x1", (w/2) + 10)
	// 	.attr("y1", h/2)
	// 	.attr("x2", (w/2) + 50)
	// 	.attr("y2", h/2);
	svg2.append("svg:line") //scale bar
		.attr("class", "pointer")
		.attr("x1", 10)
		.attr("y1", h-10)
		.attr("x2", 10+(.2*w))
		.attr("y2", h-10);
	svg2.append("text")
		.text("1.0'")
	    .attr("class", "pointertext")
	    .attr("x", 5+(.1*w))
	    .attr("y", h-20);
	// add a border
	svg2.append("rect")
		.attr("class", "graticule")
		.attr("x", 0)
		.attr("y", 0)
		.attr("height", h)
		.attr("width", w);
	// add a label to the top
	svg2.append("text")
		.text("Rough Location")
		.attr("text-anchor", "middle")
		.attr("class","pointertext")
		.attr("style", "font-size: 12px")
		.attr("y", 18)
		.attr("x", w/2);
}

var tstep = 0;
var end_shown = false;
function step_forward() {
	// take one step forward in time
	var exploding = timing_array[tstep][0];
	if (exploding) {
		if (thispage == 'sne') {
			for (var i=0;i<exploding.length;i++) { 
				// include a default size for SN with unknown mags
				if (all_objs[exploding[i]].magnitude == null) {
					var mag = 20.0;
				}
				else {
					var mag = all_objs[exploding[i]].magnitude;
				}
			    explosion(all_objs[exploding[i]].coords[0], all_objs[exploding[i]].coords[1],
				         rScale(mag), exploding[i]);
			}
		}
		else if (thispage == 'grbs') {
			for (var i=0;i<exploding.length;i++) { 
			    explosion(all_objs[exploding[i]].coords[0], all_objs[exploding[i]].coords[1],
				         [tScale(all_objs[exploding[i]].t90), rScale2(all_objs[exploding[i]].fluence)],
				         exploding[i]);
			}
		}
	}
	// move the slider and update the text
	$("#slider").slider({ value: tstep });
	document.getElementById("current_day").innerHTML = timing_array[tstep][1];
	if (tstep < timing_array.length-1) {
		tstep++;
	}
	else {
		// display the end message, if it hasn't shown yet
		if (end_shown==false) {
			$('#end_message').modal();
			end_shown = true;
		}
		pause();
	}
}

function repeat_step() {
	// take the same step again
	var exploding = timing_array[tstep][0];
	if (exploding) {
		if (thispage == 'sne') {
			for (var i=0;i<exploding.length;i++) { 
				// include a default size for SN with unknown mags
				if (all_objs[exploding[i]].magnitude == null) {
					var mag = 20.0;
				}
				else {
					var mag = all_objs[exploding[i]].magnitude;
				}
			    explosion(all_objs[exploding[i]].coords[0], all_objs[exploding[i]].coords[1],
				         rScale(mag), exploding[i]);
			}
		}
		else if (thispage == 'grbs') {
			// remove all but the largest of each exploder
			var circles = d3.selectAll('.dot')[0].concat( d3.selectAll('.activedot')[0] );
			var coords = [];
			var sizes = [];
			var indices = [];
			var current, size;
			var iii;
			for (var i=0;i<circles.length;i++) {
				current = [circles[i].cx.animVal.value, circles[i].cy.animVal.value];
				size = circles[i].r.animVal.value;
				iii = index_of(coords, current);
				if (iii<0) {
					// first time we've seen this circle
					sizes.push(size);
					coords.push(current);
					indices.push(i);
				}
				else {
					if (sizes[iii]>size) {
						// keep the earlier-identified circle
						circles[i].remove();
					}
					else {
						// remove earlier-identified circle
						circles[iii].remove();
						coords.splice(iii,1);
						sizes.splice(iii,1);
						indices.splice(iii,1);
						// keep this circle
						sizes.push(size);
						coords.push(current);
						indices.push(i);
					}
				}
				
			}
			// add in a new explosion for each
			for (var i=0;i<exploding.length;i++) { 
			    explosion(all_objs[exploding[i]].coords[0], all_objs[exploding[i]].coords[1],
				         [tScale(all_objs[exploding[i]].t90), rScale2(all_objs[exploding[i]].fluence)],
				         exploding[i]);
			}
		}
	}
	$("#slider").slider({ value: tstep });
	document.getElementById("current_day").innerHTML = timing_array[tstep][1];
}

function show_bin(i) {
	// show all pulsars in a certain timing_array bin
	// first, remove all currently-shown pulsars
	d3.selectAll('.dot').remove();
	d3.selectAll('.activedot').remove();
	// d3.selectAll('.ring').remove();
	// d3.selectAll('.activering').remove();
	for (var j=0;j<currently_pulsing.length;j++) {
		clearInterval(currently_pulsing[j]);
	}
	currently_pulsing = [];
	// now go through and add all pulsars from this bin
	var pulsing = timing_array[i][0];
	if (pulsing) {
		for (var j=0;j<pulsing.length;j++) {
			pulsar(pulsing[j]);
		}
	}
	$("#slider").slider({ value: i });
	document.getElementById("current_dist").innerHTML = timing_array[i][1];
	window.scrollTo(0,0);
	if (i==timing_array.length-1) {
		// display the end message, if it hasn't shown yet
		if (end_shown==false) {
			$('#end_message').modal();
			end_shown = true;
		}
	}
}

function go_to(objname) {
	// go to the frame of a specific explosion (snname is a string)
	for (var i=0;i<all_objs.length;i++) {
		if (all_objs[i].name == objname) {break;}
	}
	active_objs = [i];
	if (thispage != 'plsrs') {
		tstep = all_objs[i].bin;
		pause();	
	}
	else {
		show_bin(all_objs[i].bin);
	}
	window.scrollTo(0,0);
}

function highlight(objects) {
	// highlight several objects (an array of names)
	active_objs = [];
	for (var i=0;i<all_objs.length;i++) {
		if (objects.indexOf(all_objs[i].name) !== -1) {
			active_objs.push(i);
		}
	}
}

function play() {
	// restart the show!
	clearInterval(program);
	program = setInterval(step_forward, 100);
	document.getElementById("play").innerHTML = 'Pause';
	playing = true;
}

function pause() {
	// pause the show
	clearInterval(program);
	program = setInterval(repeat_step, 1000);
	document.getElementById("play").innerHTML = 'Play';
	playing = false;
}

function playpause() {
	if (playing) {
		pause();
	}
	else {
		play();
	}
}

function show_info() {
	// insert informative text into the lower div
	document.getElementById('main_txt').innerHTML = document.getElementById('about').innerHTML;
	document.getElementById('main_txt').scrollIntoView(true);
	window.scrollBy(0,-60);
}

// now define and insert everything
var width = 1000,
    height = 500;

// for SNE: map a magnitude onto a radius (pixels)
var rScale = d3.scale.linear()
    .domain([22, 0])
    .range([3,75])
    .clamp([true]);
// for GRBs: map a t90 measure onto a time (milliseconds) and a fluence onto a radius (pixels)
function tScale(t90) {
	return d3.round(50*t90); // 50 -> 1/20th of true time
}
var rScale2 = d3.scale.linear()
	.domain([0,.5])
	.range([15,75])
	.clamp([true]);
// for pulsars: map a time (s) onto another time (ms) and a flux (logscale) onto a radius (pixels)
function tScale2(period) {
	var truep = d3.round(1000*period);
	if (truep<=200) {
		return 200;
	}
	else {
		return truep;
	}
}
var rScale3 = d3.scale.linear()
	.domain([-5,5])
	.range([5,50])
	.clamp([true]);

var projection = d3.geo.equirectangular()
    .scale((width + 1) / 2 / Math.PI)
    .translate([width / 2, height / 2])
    .precision(.1);

var path = d3.geo.path()
    .projection(projection);

var graticule = d3.geo.graticule();

var svg = d3.select("#main_svg").append("svg")
    .attr("height", "100%")
    .attr("width", "100%")
	.attr("viewBox", "0 0 "+String(width)+" "+String(height));

// these gradients are used for all three types
var sngradient = svg.append("svg:defs")
  .append("svg:radialGradient")
    .attr("id", "sngradient")
    .attr("fx", "50%")
    .attr("fy", "50%")
    .attr("r", "50%");
sngradient.append("svg:stop")
    .attr("offset", "0%")
    .attr("stop-color", "white")
    .attr("stop-opacity", "1.0");
sngradient.append("svg:stop")
    .attr("offset", "100%")
    .attr("stop-color", "#999999")
    .attr("stop-opacity", "0.0");
var sngradient2 = svg.append("svg:defs")
  .append("svg:radialGradient")
    .attr("id", "sngradient2")
    .attr("fx", "50%")
    .attr("fy", "50%")
    .attr("r", "50%");
sngradient2.append("svg:stop")
    .attr("offset", "0%")
    .attr("stop-color", "#9E0022")
    .attr("stop-opacity", "1.0");
sngradient2.append("svg:stop")
    .attr("offset", "100%")
    .attr("stop-color", "#999999")
    .attr("stop-opacity", "0.0");
var grbgradient = svg.append("svg:defs")
  .append("svg:radialGradient")
    .attr("id", "grbgradient")
    .attr("fx", "50%")
    .attr("fy", "50%")
    .attr("r", "50%");
grbgradient.append("svg:stop")
    .attr("offset", "0%")
    .attr("stop-color", "white")
    .attr("stop-opacity", "1.0");
grbgradient.append("svg:stop")
    .attr("offset", "100%")
    .attr("stop-color", "#999999")
    .attr("stop-opacity", "0.0");
var grbgradient2 = svg.append("svg:defs")
  .append("svg:radialGradient")
    .attr("id", "grbgradient2")
    .attr("fx", "50%")
    .attr("fy", "50%")
    .attr("r", "50%");
grbgradient2.append("svg:stop")
    .attr("offset", "0%")
    .attr("stop-color", "#005CE6")
    .attr("stop-opacity", "1.0");
grbgradient2.append("svg:stop")
    .attr("offset", "100%")
    .attr("stop-color", "#999999")
    .attr("stop-opacity", "0.0");
var psrgradient = svg.append("svg:defs")
  .append("svg:radialGradient")
    .attr("id", "psrgradient")
    .attr("fx", "50%")
    .attr("fy", "50%")
    .attr("r", "50%");
psrgradient.append("svg:stop")
    .attr("offset", "0%")
    .attr("stop-color", "white")
    .attr("stop-opacity", "1.0");
psrgradient.append("svg:stop")
    .attr("offset", "100%")
    .attr("stop-color", "#999999")
    .attr("stop-opacity", "0.0");
var psrgradient2 = svg.append("svg:defs")
  .append("svg:radialGradient")
    .attr("id", "psrgradient2")
    .attr("fx", "50%")
    .attr("fy", "50%")
    .attr("r", "50%");
psrgradient2.append("svg:stop")
    .attr("offset", "0%")
    .attr("stop-color", "#FF9900")
    .attr("stop-opacity", "1.0");
psrgradient2.append("svg:stop")
    .attr("offset", "100%")
    .attr("stop-color", "#999999")
    .attr("stop-opacity", "0.0");

// the background image is pulled from www.eso.org/public/images/eso0932a/
svg.append("image")
	.attr("xlink:href", "img/eso0932a.jpg") 
	.attr("width", width)
	.attr("height", height);

//the intervals on the inner part of the graph
svg.append("path")
    .datum(graticule)
    .attr("class", "graticule")
    .attr("d", path);
//a border on the outside
svg.append("rect")
	.attr("x", 0)
	.attr("y", 0)
	.attr("height", height)
	.attr("width", width)
	.attr("class", "graticule");