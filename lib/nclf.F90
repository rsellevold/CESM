! NCL functions from https://github.com/NCAR/ncl/blob/develop/ni/src/lib/nfpfort

SUBROUTINE dfiltrq(nwt,ihp,fca,fcb,nsigma,wt,resp,freq)
  implicit none

  ! Input/output variables
  integer, intent(in) :: nwt, ihp
  real*8, intent(in) :: fca, fcb, nsigma
  real*8, intent(out) :: wt(nwt), resp(2*nwt-1), freq(2*nwt-1)

  ! Local variables
  integer :: nw, n, nwp1, i, j, nf
  real*8 :: work(nwt), pi, twopi, summ, frqint

  pi = 4.0*ATAN(1.0)
  twopi = 2.0*pi
  nw = (nwt-1)/2

  CALL dfilwtq(wt,nwt,nw,fca,pi,twopi,nsigma)

  if (ihp.EQ.1) then
    wt(1) = 1.0 - wt(1)
    do i=2,nw+1
      wt(i) = -wt(i)
    end do
  else if (ihp.EQ.2) then
    do i=1,nw+1
      work(i) = wt(i)
    end do
    CALL dfilwtq(wt,nwt,nw,fcb,pi,twopi,nsigma)
    do i=1,nw+1
      wt(i) = wt(i) - work(i)
    end do
  end if

  summ = 0.0
  nf = 2*nwt-1
  freq(1) = 0.0
  frqint = 0.5/dble(nf-1)

  do j=2,nw+1
    summ = summ + 2.0*wt(j)
  end do

  resp(1) = summ + wt(1)

  do i=2,nf
    summ = 0.0
    freq(i) = dble(i-1)*frqint
    do j=2,nw+1
      summ = summ + wt(j)*cos(twopi*freq(i)*dble(j-1))
    end do
    resp(i) = wt(1) + 2.0*summ
  end do

  nwp1 = nw + 1
  do n=1,nw
    work(n) = wt(n+1)
  end do
  wt(nwp1) = wt(1)
  do n=1,nw
    wt(n) = work(nwp1-n)
    wt(nwp1+n) = work(n)
  end do

  RETURN
END SUBROUTINE dfiltrq

SUBROUTINE dfilwtq(wt,nwt,nw,fc,pi,twopi,nsigma)
  implicit none

  integer, intent(in) :: nwt, nw
  real*8, intent(in) :: fc, pi, twopi, nsigma
  real*8, intent(inout) :: wt(nwt)

  integer :: i
  real*8 :: arg, fnw, sinx, siny, summ

  arg = twopi*fc
  fnw = dble(nw)

  wt(1) = 2.0*fc
  do i=1,nw
    sinx = sin(arg*dble(i)) / (pi*dble(i))
    siny = fnw*sin(dble(i)*pi/fnw) / (dble(i)*pi)
    wt(i+1) = sinx*siny*nsigma
  end do

  summ = wt(1)
  do i=2,nw+1
    summ = summ + 2.0*wt(i)
  end do
  do i=1,nw+1
    wt(i) = wt(i)/summ
  end do

  RETURN
END SUBROUTINE dfilwtq



SUBROUTINE dwgtrunave(x,npts,wgt,nwgt,kopt,xmsg,lwork,ier)
  implicit none

  integer, intent(in) :: npts, nwgt, kopt, lwork
  real*8, intent(in) :: wgt(nwgt), xmsg
  real*8, intent(inout) :: x(npts)
  integer, intent(out) :: ier

  integer :: nhalf
  real*8 :: work(lwork)

  nhalf = nwgt / 2

  CALL dwrunavx77(x,npts,wgt,nwgt,kopt,xmsg,work,lwork,ier)

  RETURN
END SUBROUTINE dwgtrunave

SUBROUTINE dwrunavx77(x,npts,wgt,nwgt,kopt,xmsg,work,lw,ier)
  implicit none

  integer, intent(in) :: npts, nwgt, kopt, lw
  real*8, intent(in) :: wgt(nwgt), xmsg
  real*8, intent(inout) :: work(lw)
  real*8, intent(inout) :: x(npts)
  integer, intent(out) :: ier

  real*8 :: wsum, summ
  integer :: n, nav, nav2, lwork, noe, kmsg, nmid, mstrt, mlast, m

  ier = 0
  if (npts.lt.1) ier = -11
  if (nwgt.gt.npts) ier = -12
  if (ier.lt.0) RETURN

  if (nwgt.le.1) then
    do n=1,npts
      work(n) = x(n)
    end do
    RETURN
  end if

  nav = nwgt
  nav2 = nav/2
  lwork = npts + 2*nav2
  noe = 0
  if (mod(nwgt,2).eq.0) noe = 1

  do n=1,lwork
    work(n) = xmsg
  end do

  do n=1,npts
    work(nav2+n) = x(n)
  end do

  wsum = 0.0
  do n=1,nwgt
    wsum = wsum + wgt(n)
  end do
  if (wsum.gt.1.0) then
    wsum = 1.0/wsum
  else
    wsum = 1.0
  end if

  if (kopt.gt.0) then
    do n=1,nav2
      work(nav2+1-n) = x(n+1)
      work(npts+nav2+n) = x(npts-n)
    end do
  else if (kopt.lt.0) then
    do n=1,nav2
      work(nav2+1-n) = x(npts+1-n)
      work(npts+nav2+n) = x(n)
    end do
  end if

  do n=1,npts
    kmsg = 0
    summ = 0.0
    nmid = n+nav2+noe
    mstrt = nmid-nav2
    mlast = mstrt+nav-1
    do m=mstrt,mlast
      if (work(m).ne.xmsg) then
        summ = summ + work(m) * wgt(m-mstrt+1)
      else
        kmsg = kmsg + 1
      end if
    end do

    if (kmsg.eq.0) then
      x(n) = summ*wsum
    else
      x(n) = xmsg
    end if
  end do

  RETURN
END SUBROUTINE dwrunavx77


SUBROUTINE vinth2p_ecmwf(dati, dato, hbcofa, hbcofb, &
                         p0, plevo, intyp, &
                         ilev, psfc, spvl, kxtrp, &
                         imax, nlat, nlevi, nlevip1, &
                         nlevo, nt, varflg, tbot, phis)
  use omp_lib
  implicit none

  integer, intent(in) :: intyp, ilev, kxtrp, imax, nlat
  integer, intent(in) :: nlevi, nlevip1, nlevo, nt, varflg

  real*4, intent(in) :: dati(imax,nlat,nlevi,nt)
  real*4, intent(in) :: hbcofa(nlevip1), hbcofb(nlevip1)
  real*4, intent(in) :: p0, spvl
  real*4, intent(in) :: plevo(nlevo)
  real*4, intent(in) :: psfc(imax,nlat,nt), phis(imax,nlat,nt)
  real*4, intent(in) :: tbot(imax,nlat,nt)
  real*4, intent(out) :: dato(imax,nlat,nlevo,nt)

  integer :: i, j, k, t, kp, kpi, iprint
  real*4 :: tstar, hgt, alnp, t0, tplat, &
            tprime0, alpha, alph, psfcmb, &
            plevi(nlevip1)
  real*4 :: rd, ginv

  rd = 287.0
  ginv = 1.0 / 9.80616
  alpha = 0.0065 * rd * ginv

  do t=1,nt
    do 70 j=1,nlat
      do 60 i=1,imax

        if (psfc(i,j,t)==spvl) then
          do k=1,nlevo
            dato(i,j,k,t) = spvl
          end do
          go to 60
        end if

        do k=1,nlevi
          kpi = k
          plevi(k) = (hbcofa(kpi)*p0) + hbcofb(kpi) * (psfc(i,j,t)*.01)
        end do

        do 50 k=1,nlevo
          
          if (plevo(k)<plevi(1)) then
            kp = 1
            go to 30
          else if (plevo(k)>plevi(nlevi)) then
            if (kxtrp==0) then
              dato(i,j,k,t) = spvl
              go to 40
            else if (varflg>0) then
              psfcmb = psfc(i,j,t)*0.01
              tstar = dati(i,j,nlevi,t) * &
                      (1.0+alpha* (psfcmb/plevi(nlevi)-1))
              hgt = phis(i,j,t) * ginv
              if (hgt<2000.0) then
                alnp = alpha*log(plevo(k)/psfcmb)
              else
                t0 = tstar + 0.0065*hgt
                tplat = min(t0, 298.0)
                if (hgt < 2500.0) then
                  tprime0 = 0.002*((2500.0-hgt)*t0+ (hgt-2000.0)*tplat)
                else
                  tprime0 = tplat
                end if
                if (tprime0<tstar) then
                  alnp = 0.0
                else
                  alnp = rd* (tprime0-tstar)/phis(i,j,t)*log(plevo(k)/psfcmb)
                end if
                dato(i,j,k,t) = tstar* (1.0+alnp+0.5*alnp**2+1.0/6.0*alnp**3)
                go to 40
              end if
            else if (varflg < 0) then
              psfcmb = psfc(i,j,t)*0.01
              hgt = phis(i,j,t) * ginv
              tstar = tbot(i,j,t)* (1.0+alpha* (psfcmb/plevi(nlevi)-1.0))
              t0 = tstar + 0.0065*hgt
              if (tstar<290.5 .and. t0>290.5) then
                alph = rd/phis(i,j,t)* (290.5-tstar)
              else if (tstar>290.5 .and. t0>290.5) then
                alph = 0
                tstar = 0.5* (290.5+tstar)
              else
                alph = alpha
              end if
              if (tstar < 255.0) then
                tstar = 0.5* (tstar+255.0)
              end if
              alnp = alph*log(plevo(k)/psfcmb)
              dato(i,j,k,t) = hgt - rd*tstar*ginv*log(plevo(k)/psfcmb)*(1.0+.5*alnp+1.0/6.0*alnp**2)
              go to 40
            else
              dato(i,j,k,t) = dati(i,j,nlevi,t)
              go to 40
            end if
          else if (plevo(k)>plevi(nlevi-1)) then
            kp = nlevi - 1
            go to 30
          else
            kp = 0
 20         continue
            kp = kp+1
            if (plevo(k)<plevi(kp+1)) go to 30
            if (kp>nlevi) then
              write(6, fmt=25) kp, nlevi
 25           format(' KP.GT.KLEVI IN P2HBD. KP,KLEVI= ', 2I5)
            end if
            go to 20
          end if
 30       continue

          if (intyp==1) then
            dato(i,j,k,t) = dati(i,j,kp,t) + (dati(i,j,kp+1,t)-dati(i,j,kp,t))*(plevo(k)-plevi(kp))/(plevi(kp+1)-plevi(kp))
          else if (intyp==2) then
            iprint = 1
            dato(i,j,k,t) = dati(i,j,kp,t) + (dati(i,j,kp+1,t)-dati(i,j,kp,t))*log(plevo(k)/plevi(kp))/log(plevi(kp+1)/plevi(kp))
          end if
 40       continue
 50     continue
 60   continue
 70 continue
  end do

  return
  END SUBROUTINE vinth2p_ecmwf
