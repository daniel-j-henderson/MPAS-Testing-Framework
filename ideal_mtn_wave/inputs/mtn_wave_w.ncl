load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"

begin

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


  wks = gsn_open_wks("pdf","mtn_wave_w")
  ;gsn_define_colormap(wks,"gui_default")

  f = addfile("./output.nc","r")

  res                      = True
  res@gsnDraw              = False
  res@gsnFrame             = False

  res@vpXF      = 0.15
  res@vpYF      = 0.75
  res@vpWidthF  = 0.7
  res@vpHeightF = 0.5

  res@trYMinF =  0.
  res@trYMaxF = 10.
  res@trXMinF = -25.
  res@trXMaxF =  25.

  zgrid = f->zgrid(:,:)/1000.

  xCell = f->xCell(:)/1000. - 100. 
  yCell = f->yCell(:)/1000. 
 
  plot_zgrid1 = new((/71,200/),double)
           x1 = new((/201/),   double)
  plot_zgrid2 = new((/71,200/),double)
           x2 = new((/200/),   double)
  plot_zgrid  = new((/71,400/),double)
           x  = new((/400/),   double)

  nCells = dimsizes(xCell) 
  cnt1=0
  cnt2=0
  do iCell=0,nCells-1  
     if (yCell(iCell).ge.0.2 .and. yCell(iCell).le.0.3 )then
       plot_zgrid1(:,cnt1) = zgrid(iCell,:)   
                x1(cnt1)   = xCell(iCell) 
       cnt1 = cnt1+1
     end if
     if (yCell(iCell).ge.0.5 .and. yCell(iCell).le.0.6 )then
       plot_zgrid2(:,cnt2) = zgrid(iCell,:)   
                x2(cnt2)   = xCell(iCell)
       cnt2 = cnt2+1
     end if
  end do

  do i=0,cnt1-1
     ii=2*i
     plot_zgrid(:,ii) = plot_zgrid1(:,i)
            x(ii)  = x1(i)
  end do
  do i=0,cnt2-1
     ii=2*i+1
     plot_zgrid(:,ii) = plot_zgrid2(:,i)
            x(ii)  = x2(i)
  end do

  plot1 = gsn_csm_xy(wks,x,plot_zgrid(0,:),res)

  z = ndtooned(plot_zgrid)
  res@sfYArray = z
  xarray = onedtond(x,(/71,400/))
  xx = ndtooned(xarray)
  res@sfXArray = xx

  res@gsnRightString     = ":F21:MPAS Schaer test"
  res@gsnRightStringFontHeightF = 0.019
  res@tiYAxisString = ":F21:z(km)"
  res@tiYAxisFontHeightF = 0.017
  res@tiXAxisString = ":F21:x(km)"
  res@tiXAxisFontHeightF = 0.017

  plot_var1 = new((/71,200/),double)
  plot_var2 = new((/71,200/),double)
  plot_var  = new((/71,400/),double)

  dt = 1800
  nTime = 11
  do Time=0,nTime-1

  w = f->w(Time,:,:)
  cnt1=0
  cnt2=0
  do iCell=0,nCells-1  
     if (yCell(iCell).ge.0.2 .and. yCell(iCell).le.0.3 )then
       plot_var1(:,cnt1) = w(iCell,:) 
       cnt1 = cnt1+1
     end if
     if (yCell(iCell).ge.0.5 .and. yCell(iCell).le.0.6 )then
       plot_var2(:,cnt2) = w(iCell,:) 
       cnt2 = cnt2+1
     end if
  end do

  do i=0,cnt1-1
     ii=2*i
     plot_var(:,ii) = plot_var1(:,i)
  end do
  do i=0,cnt2-1
     ii=2*i+1
     plot_var(:,ii) = plot_var2(:,i)
  end do
  fld = ndtooned(plot_var)

  time = dt*Time
  res@gsnLeftString     = ":F22:w :F21:at "+time+"s"
  res@gsnLeftStringFontHeightF = 0.019
  res@cnLevelSelectionMode = "ManualLevels"
  res@cnMinLevelValF       =  -2.0
  res@cnMaxLevelValF       =   2.0
  res@cnLevelSpacingF      =   0.05
  res@gsnContourZeroLineThicknessF = 0.
  res@cnLineLabelsOn       =   False

  res@gsnContourNegLineDashPattern = 1

  plot1 = gsn_csm_contour(wks,fld,res)

  poly_res                  = True
  poly_res@gsLineThicknessF = 2.
  poly_res@gsLineColor      = "black"
  poly_res@gsFillColor      = "gray"
  zpts     = plot_zgrid(0,:)
  xpts     = x(:) 
  dummy1= gsn_add_polygon(wks,plot1,xpts,zpts,poly_res)
  dummy2= gsn_add_polyline(wks,plot1,xpts,zpts,poly_res)
  
  draw(plot1)
  frame(wks)

  end do

end
