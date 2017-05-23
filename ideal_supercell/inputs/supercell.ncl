load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"

begin

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


  r2d = 57.2957795             ; radians to degrees

  wks = gsn_open_wks("pdf","supercell")

  f = addfile("output.nc","r")

  alpha = f->angleEdge(:)
  xCell   = f->xCell(:)/1000.
  yCell   = f->yCell(:)/1000.


  res                      = True
  res@gsnMaximize          = True
  res@gsnSpreadColors      = True

  res@sfXArray             = xCell
  res@sfYArray             = yCell

  res@tiXAxisFontHeightF   = 0.018
  res@tiXAxisString        =":F21:X (km)"
  res@tiYAxisFontHeightF   = 0.018
  res@tiYAxisString        =":F21:Y (km)"
  res@tmXBPrecision        = 2
  res@tmYLPrecision        = 2

  Time = 4 
  iTime = Time*300
  res@gsnRightString     = ":F26: MPAS"
  res@gsnRightStringFontHeightF = 0.014
  res@gsnContourNegLineDashPattern = 1

  res@cnLevelSelectionMode = "ManualLevels"
  res@cnMinLevelValF       =  -6.0
  res@cnMaxLevelValF       =   6.0
  res@cnLevelSpacingF      =   0.3 
  res@cnFillOn             = True
  res@cnLinesOn            = True
  res@cnLineLabelsOn       = True
  ;res@cnInfoLabelOn        = False
  res@lbLabelBarOn         = False

  ;res@lbLabelAutoStride    = True
  ;res@lbBoxLinesOn         = False

  gsn_define_colormap(wks,"testcmap")
  
  res@gsnSpreadColorStart        =   1
  res@gsnSpreadColorEnd          = 201

  k=4
  Level = k+1
  res@cnMinLevelValF       =  -2.4
  res@cnMaxLevelValF       =   2.4
  res@cnLevelSpacingF      =   0.2 
  res@gsnLeftString     = ":F33:q:F35:):F21::B:Level "+ Level +":N: at " + iTime +"s" 

  h = f->theta(Time,:,k)
  h0= f->theta_base(Time,:,k)
  qv= f->qv(Time,:,k)
  qv0= f->qv(0,:,k)

  fld = h/(1.+1.61*qv) - h0/(1.+1.61*qv0) 
  res@cnLineDashPattern = 0
  plot = gsn_csm_contour(wks,fld,res)

end

