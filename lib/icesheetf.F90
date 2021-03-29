SUBROUTINE cism2clm(x,clat,ncy,clon,ncx,ilat,niy,ilon,nix,dataout)
  implicit none

  integer :: cx, cy, ix, iy
  real*8 :: dclat, dclon

  integer, intent(in) :: ncy, ncx, niy, nix
  real*8, intent(in) :: clat(ncy), clon(ncx)
  real*8, intent(in) :: ilat(niy,nix), ilon(niy,nix)
  real*8, intent(in) :: x(niy,nix)
  real*8, intent(out) :: dataout(ncy,ncx)

  dclat = 180/(ncy * 2.0)
  dclon = 360/(ncx * 2.0)

  ! Initialize CLM array with zeros
  do cx=1,ncx
    do cy=1,ncy
      dataout(cy,cx) = 0.0
    end do
  end do

  do ix=1,nix
    do iy=1,niy
      do cx=1,ncx
        do cy=1,ncy
          if ((clat(cy)-dclat)<=ilat(iy,ix)) then
            if ((ilat(iy,ix))<=(clat(cy)+dclat)) then
              if ((clon(cx)-dclon)<=ilon(iy,ix)) then
                if ((ilon(iy,ix))<=(clon(cx)+dclon)) then
                  if (x(iy,ix)>0.0) then
                    dataout(cy,cx) = dataout(cy,cx) + 1.0
                  end if
                end if
              end if
            end if
          end if
        end do
      end do
    end do
  end do

  RETURN
END SUBROUTINE cism2clm
