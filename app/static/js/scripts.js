// to run this directly in terminal, in git:
// $ node <filename.js>
// i.e.:  node scratch.js

console.log('script loaded');

// This function is called from index.html
function load_snotel_site_metadata(site_data_list){
  return site_data_list
}

///////////////////////////////////////////////////////////////////////////////////////////////////

window.onload = function() {


    // region tab selection form element 
    var stateSelReg = document.getElementById("regionplots-state-select");
    var zoneSelReg = document.getElementById("regionplots-zone-select");
    var buildBtnReg = document.getElementById("regionplots-build-plots-btn");

    // site tab selection form elements
    var stateSelSite = document.getElementById("siteplots-state-select");
    var zoneSelSite =  document.getElementById("siteplots-zone-select");
    var siteSelSite =  document.getElementById("siteplots-site-select");
    var buildBtnSite = document.getElementById("siteplots-build-plots-btn");

    // get the list of unique states from the sites data object array
    const stateArr = [... new Set(siteDataArr.map( (objArr) => objArr.stationState)) ].sort();

    // popluate state select boxes from sites_data.json state list

    // state select on the Regions tab
    for(var i = 0; i < stateArr.length; i++) {
        var opt = document.createElement('option');
        opt.innerHTML = stateArr[i];
        opt.value = stateArr[i];
        stateSelReg.appendChild(opt);
    }
    // state select on the Sites tab
    for(var i = 0; i < stateArr.length; i++) {
        var opt = document.createElement('option');
        opt.innerHTML = stateArr[i];
        opt.value = stateArr[i];
        stateSelSite.appendChild(opt);
    }


    // When state is selected, dynamically change the region options

    // TODO: Some sites have multiple regions/zones, which returns redundant options in the filter tabs,
    // need to implement an operation that separates these strings and just finds unique values, then populates
    // the filters with unique values. Then in the callback function to the view, need to filter using an 'in' 
    // operation rather than a '==' operation

    stateSelReg.onchange = function() {
        let stateChoice = stateSelReg.value
        console.log("state select choice is " + stateChoice)

        // TODO: change the state select on the sites tab to the one that has been selected on the region tab, only if one hasnt been chosen already
        // something like if first option 'selectState' is selected currently, getElementByID('stateSelSite')>child>value==stateChoice, add property 'selected'

        // Filter the zones from the selected state and populate the zone select menu:
        // FIirst get the js objects just from that state
        let stateSitesArr = siteDataArr.filter(objArr => objArr.stationState===stateChoice).sort();

        // Next, get the zones from those js objects
        let zoneArr =  [... new Set(stateSitesArr.map( (objArr) => objArr.stationZone))];
        // Some zone entries contain more than one zone, concatenated by a semi colon ;
        // join all zonees, break them back apart, and return the unique values sorted into a new array
        zoneArr = [... new Set(zoneArr.join(';').split(';').sort())];
        
        zoneSelReg.options.length = 0;
        for(var i = 0; i < zoneArr.length; i++) {
            var opt = document.createElement('option');
            opt.innerHTML = zoneArr[i];
            opt.value = zoneArr[i];
            zoneSelReg.appendChild(opt);
        }

      }

       //   filter the site plot zone and site select menus when state is chosen 

      stateSelSite.onchange = function() {
        let stateChoice = stateSelSite.value
        console.log("state select choice for region and site filter is " + stateChoice)
        // filter the zones from the selected state and populate the zone select menus
        let stateSitesArr = siteDataArr.filter(objArr => objArr.stationState===stateChoice).sort();
        let zoneArr =  [... new Set(stateSitesArr.map( (objArr) => objArr.stationZone))].sort();
        // some sites have multiple zones, break these strings apart and just return an array of unique zone values
        zoneArr = [... new Set(zoneArr.join(';').split(';').sort())];

        // TODO: figure out how to resort the site ID after sorting the site name; or else use the site name as the parameter to
        // pass to the callback function
        let siteNameArr =  [... new Set(stateSitesArr.map( (objArr) => objArr.stationName))].sort();
        let siteIdArr =  [... new Set(stateSitesArr.map( (objArr) => objArr.stationID))];

        zoneSelSite.options.length = 0;
        for(var i = 0; i < zoneArr.length; i++) {
            var opt = document.createElement('option');
            opt.innerHTML = zoneArr[i];
            opt.value = zoneArr[i];
            zoneSelSite.appendChild(opt);
        }

        siteSelSite.options.length = 0;
        for(var i = 0; i < siteNameArr.length; i++) {
            var opt = document.createElement('option');
            opt.innerHTML = siteNameArr[i];
            opt.value = siteNameArr[i];
            siteSelSite.appendChild(opt);
        }

      }

      // filter the site plot site select menu when a zone is chosen
      zoneSelSite.onchange = function () {
        let zoneChoice = zoneSelSite.value
        console.log("zone choice is " + zoneChoice)
        // let zoneSitesArr = siteDataArr.filter(objArr => objArr.stationZone===zoneChoice);
        let zoneSitesArr = siteDataArr.filter(objArr => objArr.stationZone.includes(zoneChoice)); //filter for the zone substring in the (potentially) multi-zone string
        let siteNameArr =  [... new Set(zoneSitesArr.map( (objArr) => objArr.stationName))].sort();
        let siteIdArr =  [... new Set(zoneSitesArr.map( (objArr) => objArr.stationID))];

        siteSelSite.options.length = 0; /*clear the selection box*/
        for(var i = 0; i < siteNameArr.length; i++) {
            var opt = document.createElement('option');
            opt.innerHTML = siteNameArr[i];
            // opt.value = siteIdArr[i];
            opt.value = siteNameArr[i];
            siteSelSite.appendChild(opt);
        }
      }
     
    
    buildBtnReg.onclick = function() {

        console.log("Calling SNOTEL webservice and building region plots...");

        document.getElementById('new-snow-plot').innerHTML = '';
        document.getElementById('depth-plot').innerHTML = '';
        document.getElementById('temp-plot').innerHTML = '';
        document.getElementById('season-plot').innerHTML = '';

        let stateChoice = stateSelReg.value;
        let zoneChoice = zoneSelReg.value;
        
        if (zoneChoice == 'selectzone') {
            alert("Please select a zone to activate plots");
            return;
        } else {
            console.log("Building plots for " + stateChoice + ', ' + zoneChoice + ' zone.');
            region_plots_callback(zone=zoneChoice)
        }

    }


    buildBtnSite.onclick = function() {

        console.log("building site plots");

        document.getElementById('seasonal-snow-meteogram-plot').innerHTML = '';
        document.getElementById('seasonal-temperature-plot').innerHTML = '';
        document.getElementById('7d-wind-plot').innerHTML = '';
        document.getElementById('SWE-regime-plot').innerHTML = '';

        let siteChoice = siteSelSite.value;
    
        if (siteChoice == 'selectsite') {
            alert("Please select an indvidual site to build plots");
            return;
        } else {
            console.log("Building plots for " + siteChoice);
            site_plots_callback(site_id=siteChoice) 
            SWE_regime_callback(site_id=siteChoice)
        }
    }

}


// ----------------------------------------------------------------------------------------------------------

// REGIONAL PLOTS CALLBACK 

async function region_plots_callback(zone) {
    // send them to the callback url to do use in filtering tables and returning flow table
    route_url = 'build_regional_plots_cb?zone=' + zone 
    console.log('route url is: ' + route_url)

    document.getElementById('new-snow-plot').innerHTML = "Calling SNOTEL webservice and building regional plots, this may take a moment...";

    let response = await fetch(route_url);
    if (response.ok) {
      let plotsJSON = await response.json();
      console.log('recieved new plot html for ' + zone + ', updating page');
      
    //   todo: loop this below, or else, if the data object on the server side
    // can be created just once, call each of these asynchronously so that they
    // can fail individually if needed
      
      newSnowPlotJSON = plotsJSON['new-snow-plot'];
      tempPlotJSON = plotsJSON['depth-plot'];
      depthPlotJSON = plotsJSON['temp-plot'];
      seasonPlotJSON = plotsJSON['season-plot'];
    
      var my_config = {
        'responsive': true,
        'displayModeBar': false
      };

      document.getElementById('new-snow-plot').innerHTML = '';
      Plotly.newPlot('new-snow-plot', newSnowPlotJSON, config=my_config);

      document.getElementById('temp-plot').innerHTML ='';
      Plotly.newPlot('temp-plot', depthPlotJSON, config=my_config);

      document.getElementById('depth-plot').innerHTML = '';
      Plotly.newPlot('depth-plot', tempPlotJSON, config=my_config);

      document.getElementById('season-plot').innerHTML = '';
      Plotly.newPlot('season-plot', seasonPlotJSON, config=my_config);

    } else {
      alert("HTTP-Error: " + response.status + " on region plots build");
    }
  }

  // ----------------------------------------------------------------------------------------------------------

// INDIVIDUAL SITE PLOTS CALLBACK 

async function site_plots_callback(site) {
    // send them to the callback url to do use in filtering tables and returning flow table
    route_url = 'build_site_plots_cb?site=' + site 
    console.log('route url is: ' + route_url)

    document.getElementById('seasonal-snow-meteogram-plot').innerHTML = "Calling SNOTEL webservice and building site plots, this may take a moment..." + site;

    let response = await fetch(route_url);
    if (response.ok) {
      let plotsJSON = await response.json();
      console.log('recieved new plot html for ' + site + ', updating page');
      
    // TODO: loop this below, or else, if the data object on the server side
    // can be created just once, call each of these asynchronously so that they
    // can fail individually if needed
      
    seasonalMeteogramPlotJSON = plotsJSON['seasonal_meteogram_plot'];
    seasonalTemperaturePlotJSON = plotsJSON['seasonal_temperature_plot'];
    windPlotJSON = plotsJSON['wind_history_plot'];
    
    //   tempPlotJSON = plotsJSON['depth-plot'];
    //   depthPlotJSON = plotsJSON['temp-plot'];
    //   seasonPlotJSON = plotsJSON['season-plot'];
    
      var my_config = {
        'responsive': true,
        'displayModeBar': false
      };

      document.getElementById('seasonal-snow-meteogram-plot').innerHTML = '';
      Plotly.newPlot('seasonal-snow-meteogram-plot', seasonalMeteogramPlotJSON, config=my_config);

      document.getElementById('seasonal-temperature-plot').innerHTML = '';
      Plotly.newPlot('seasonal-temperature-plot', seasonalTemperaturePlotJSON, config=my_config);

      document.getElementById('seasonal-wind-plot').innerHTML = '';
      if(windPlotJSON === "No wind data available at this site"){
        document.getElementById('seasonal-wind-plot').innerHTML = 'No wind data available for this site';
      } else {
        console.log(windPlotJSON);
        Plotly.newPlot('seasonal-wind-plot', windPlotJSON, config=my_config);
      }
        
    } else {
      alert("HTTP-Error: " + response.status + " on region plots build");
    }
  }


// SWE regime plot gets its on cb because it is significantly slower to build...
async function SWE_regime_callback(site) {
    // send them to the callback url to do use in filtering tables and returning flow table
  route_url = 'build_SWE_regime_cb?site=' + site 
  console.log('route url is: ' + route_url)

  document.getElementById('SWE-regime-plot').innerHTML = "Constructing historical SWE plot..." + site;

  let response = await fetch(route_url);
  if (response.ok) {
    let plotsJSON = await response.json();
    console.log('recieved new SWE plot html for ' + site + ', updating page');
    
  // TODO: loop this below, or else, if the data object on the server side
  // can be created just once, call each of these asynchronously so that they
  // can fail individually if needed
    
  sweRegimePlotJSON = plotsJSON['SWE_regime_plot_JSON'];
  
    var my_config = {
      'responsive': true,
      'displayModeBar': false
    };

    document.getElementById('SWE-regime-plot').innerHTML = '';
    Plotly.newPlot('SWE-regime-plot', sweRegimePlotJSON, config=my_config);
  
  } else {
    alert("HTTP-Error: " + response.status + " on SWE plots build");
  }
}



