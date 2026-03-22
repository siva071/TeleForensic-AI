def build_map(tower_df, scores):
  if tower_df is None:
    return None
  
  try:
    import folium
    import math
    from folium.plugins import MarkerCluster
    
    # Build scores lookup
    scores_lookup = {}
    if scores:
      for s in scores:
        scores_lookup[str(s.get(
          'number',''))] = s
    
    # Get color by risk
    def get_color(phone):
      phone = str(phone)
      if phone in scores_lookup:
        label = scores_lookup[phone].get(
          'label','')
        if label == 'HIGH RISK':
          return 'red'
        elif label == 'Medium':
          return 'orange'
        else:
          return 'green'
      return 'blue'
    
    def get_score(phone):
      phone = str(phone)
      if phone in scores_lookup:
        return scores_lookup[phone].get(
          'score', 0)
      return 0
    
    # Find lat/lon columns
    lat_col = None
    lon_col = None
    phone_col = None
    tower_col = None
    area_col = None
    
    for col in tower_df.columns:
      cl = col.lower()
      if 'lat' in cl:
        lat_col = col
      elif 'lon' in cl or 'lng' in cl:
        lon_col = col
      elif 'phone' in cl or 'number' in cl:
        phone_col = col
      elif 'tower' in cl or 'bts' in cl:
        tower_col = col
      elif 'area' in cl or 'location' in cl:
        area_col = col
    
    if not lat_col or not lon_col:
      return None
    
    # Center map on mean coordinates
    center_lat = tower_df[lat_col].mean()
    center_lon = tower_df[lon_col].mean()
    
    m = folium.Map(
      location=[center_lat, center_lon],
      zoom_start=7,
      tiles='OpenStreetMap')
    
    # Group by tower location
    tower_groups = tower_df.groupby(
      [lat_col, lon_col])
    
    # Hexagonal offset pattern
    # For multiple phones at same tower
    hex_offsets = [
      (0, 0),
      (0.008, 0),
      (-0.008, 0),
      (0.004, 0.007),
      (-0.004, 0.007),
      (0.004, -0.007),
      (-0.004, -0.007),
    ]
    
    for (lat, lon), group in tower_groups:
      try:
        lat = float(lat)
        lon = float(lon)
      except:
        continue
      
      # Get tower info
      tower_id = group[tower_col].iloc[0] \
        if tower_col else 'Unknown'
      area = group[area_col].iloc[0] \
        if area_col else 'Unknown'
      
      phones_at_tower = group[
        phone_col].unique().tolist() \
        if phone_col else []
      
      # Draw hexagonal tower shape
      # Hexagon points
      hex_points = []
      hex_size = 0.003
      for i in range(6):
        angle = math.radians(60 * i - 30)
        hx = lat + hex_size * math.cos(angle)
        hy = lon + hex_size * math.sin(angle)
        hex_points.append([hx, hy])
      hex_points.append(hex_points[0])
      
      # Color hexagon by highest risk
      hex_color = 'blue'
      max_score = 0
      for ph in phones_at_tower:
        sc = get_score(ph)
        if sc > max_score:
          max_score = sc
          hex_color = get_color(ph)
      
      # Draw hexagon
      folium.Polygon(
        locations=hex_points,
        color=hex_color,
        fill=True,
        fill_color=hex_color,
        fill_opacity=0.3,
        weight=2,
        tooltip=f"Tower: {tower_id} | Area: {area}"
      ).add_to(m)
      
      # Tower center marker
      tower_popup = f"""
        <div style='font-family:Arial;
                    min-width:200px'>
          <h4 style='color:#1a1a2e;
                     margin:0'>
            Tower: {tower_id}
          </h4>
          <hr style='margin:5px 0'>
          <b>Area:</b> {area}<br>
          <b>Location:</b> 
            {lat:.4f}, {lon:.4f}<br>
          <b>Numbers at tower:</b> 
            {len(phones_at_tower)}<br>
          <hr style='margin:5px 0'>
      """
      
      # Add each phone with risk
      for ph in phones_at_tower:
        color = get_color(str(ph))
        score = get_score(str(ph))
        color_circle = {
          'red': '[HIGH]',
          'orange': '[MED]',
          'green': '[LOW]',
          'blue': '[-]'}.get(color, '[-]')
        tower_popup += f"""
          <div style='margin:3px 0'>
            {color_circle} 
            <b>{ph}</b> 
            (Score: {score})
          </div>
        """
      
      tower_popup += "</div>"
      
      # Tower icon
      tower_icon = folium.DivIcon(
        html=f"""
          <div style='
            background:{hex_color};
            border:2px solid white;
            border-radius:50%;
            width:20px;height:20px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:10px;
            font-weight:bold;
            color:white;
            box-shadow:0 2px 4px rgba(0,0,0,0.4)
          '>T</div>
        """,
        icon_size=(24, 24),
        icon_anchor=(12, 12))
      
      folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(
          tower_popup, max_width=250),
        tooltip=f"Tower: {tower_id} | Area: {area} | Numbers: {len(phones_at_tower)}",
        icon=tower_icon
      ).add_to(m)
      
      # Phone markers around tower
      # in hexagonal pattern
      for idx, phone in enumerate(
        phones_at_tower[:6]):
        
        offset = hex_offsets[idx + 1]
        ph_lat = lat + offset[0]
        ph_lon = lon + offset[1]
        
        ph_color = get_color(str(phone))
        ph_score = get_score(str(phone))
        
        # Draw line from phone to tower
        # (distance line)
        dist_km = round(
          math.sqrt(
            (offset[0] * 111) ** 2 +
            (offset[1] * 111 * 
             math.cos(math.radians(lat))
            ) ** 2
          ), 3)
        
        folium.PolyLine(
          locations=[
            [lat, lon],
            [ph_lat, ph_lon]],
          color=ph_color,
          weight=1.5,
          opacity=0.6,
          tooltip=f"Distance: {dist_km} km",
          dash_array='5'
        ).add_to(m)
        
        # Phone marker
        phone_popup = f"""
          <div style='font-family:Arial;
                      min-width:180px'>
            <h4 style='margin:0;
                       color:{ph_color}'>
              Phone: {phone}
            </h4>
            <hr style='margin:5px 0'>
            <b>Risk Score:</b> 
              {ph_score}/100<br>
            <b>Connected Tower:</b> 
              {tower_id}<br>
            <b>Area:</b> {area}<br>
            <b>Tower Distance:</b> 
              ~{dist_km} km
          </div>
        """
        
        # Color map for circle
        circle_color = {
          'red': '#FF4444',
          'orange': '#FFA500',
          'green': '#44BB44',
          'blue': '#4444FF'
        }.get(ph_color, '#888888')
        
        phone_icon = folium.DivIcon(
          html=f"""
            <div style='
              background:{circle_color};
              border:2px solid white;
              border-radius:50%;
              width:16px;height:16px;
              display:flex;
              align-items:center;
              justify-content:center;
              font-size:8px;
              font-weight:bold;
              color:white;
              box-shadow:0 2px 4px rgba(0,0,0,0.4)
            '>P</div>
          """,
          icon_size=(20, 20),
          icon_anchor=(10, 10))
        
        folium.Marker(
          location=[ph_lat, ph_lon],
          popup=folium.Popup(
            phone_popup, max_width=220),
          tooltip=f"Phone: {phone} | Score: {ph_score}/100 | Risk: {ph_color.upper()}",
          icon=phone_icon
        ).add_to(m)
    
    # Enhanced Legend
    legend_html = """
<div style='
  position:fixed;
  bottom:30px;left:30px;
  z-index:1000;
  background:white;
  padding:12px 16px;
  border-radius:8px;
  border:2px solid #ccc;
  font-family:Arial;
  font-size:12px;
  box-shadow:0 2px 8px rgba(0,0,0,0.3)
'>
  <b style='font-size:13px'>
    TeleForensic AI Map
  </b><br><br>
  <b>Tower Risk Levels:</b><br>
  <span style='color:red;font-size:16px'>
    &#9679;</span> High Risk Tower<br>
  <span style='color:orange;font-size:16px'>
    &#9679;</span> Medium Risk Tower<br>
  <span style='color:green;font-size:16px'>
    &#9679;</span> Low Risk Tower<br>
  <span style='color:blue;font-size:16px'>
    &#9679;</span> Unknown Risk<br>
  <br>
  <b>Markers:</b><br>
  <b style='color:#333'>T</b> 
    &nbsp;BTS Tower Location<br>
  <b style='color:#333'>P</b> 
    &nbsp;Phone Location<br>
  <span style='color:#999'>&#11041;</span>
    &nbsp;Hexagonal Coverage<br>
  <span style='color:#999'>----</span>
    &nbsp;Tower-Phone Distance
</div>
"""
    m.get_root().html.add_child(
      folium.Element(legend_html))
    
    m.save('map.html')
    return 'map.html'
  
  except Exception as e:
    print(f"Map error: {e}")
    return None