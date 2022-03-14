from astropy.coordinates import Angle, SkyCoord


def calc_pa(ra: Angle, dec: Angle, ra0: Angle, dec0: Angle):
    """
    Calculates position angle of object at (ra, dec) from center at (ra0, dec0).

    Args:
        ra (astropy.coordinates.Angle): Right Ascension of target in J2000 radians.
        dec (astropy.coordinates.Angle): Declination of target in J2000 radians.
        ra0 (astropy.coordinates.Angle): Right Ascension of center in J2000 radians.
        dec0 (astropy.coordinates.Angle): Declination of center in J2000 radians.

    Returns:
        Position angle of object in radians (astropy.coordinates.Angle).
    """

    return SkyCoord(ra=ra0, dec=dec0).position_angle(SkyCoord(ra=ra, dec=dec))

