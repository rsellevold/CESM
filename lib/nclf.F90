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


!SUBROUTINE vinth2p(dati, dato, hbcofa, hbcofb, p0, plevi, plevo, &
!                   intyp, ilev, psfc, spvl, kxtrp, imax, nlat, &
!                   nlevi, nlevip1, nlevo)
!  use omp_lib
!  implicit none
