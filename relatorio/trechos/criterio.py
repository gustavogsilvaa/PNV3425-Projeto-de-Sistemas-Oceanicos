def criterio_areas(phd, GZ, HA, phal):
    d = GZ - HA
    phi1 = phi2 = None
    for i in range(1, len(phd)):
        if phi1 is None and d[i - 1] < 0 <= d[i]:
            phi1 = phd[i - 1] + (phd[i] - phd[i - 1]) * d[i - 1] / (d[i - 1] - d[i])
        elif phi1 is not None and d[i - 1] > 0 >= d[i]:
            phi2 = phd[i - 1] + (phd[i] - phd[i - 1]) * d[i - 1] / (d[i - 1] - d[i])
            break
    if phal <= 0:
        return dict(phi1=phi1, phi2=phi2, A=0.0, B=0.0, AB=0.0, GZ_min=0.0,
                    GZsen_min=-1.0, lim_gz=0.0)
    m = phd < phal
    xs = np.radians(np.append(phd[m], phal))
    A = trapezoid(np.append(GZ[m], np.interp(phal, phd, GZ)), xs)
    B = trapezoid(np.append(HA[m], np.interp(phal, phd, HA)), xs)
    lim = phi2 if (phi2 is not None and phi2 < phal) else phal
    sel = (phd > 0) & (phd <= lim)
    if not sel.any():
        sel = (phd > 0) & (phd <= phd[1])
    gz_sel = GZ[sel]
    gzsen = gz_sel / np.sin(np.radians(phd[sel]))
    return dict(phi1=phi1, phi2=phi2, A=A, B=B, AB=A / B if B > 0 else np.inf,
                GZ_min=gz_sel.min(), GZsen_min=gzsen.min(), lim_gz=lim)


def estabilidade(x, hid, pes, cen, dphi=1.0, phimax=50.0):
    V0, KG, Dg = hid["V"], pes["KG"], hid["Delta"] * G
    out = dict(vento={})
    AB_min, gzsen_min = np.inf, np.inf
    for plano in PLANOS:
        # [REV 1] tabela de vento depende do plano (z_CLR)
        ventos = {nome: tabela_vento(x, V, plano, cen) for nome, V in VENTOS.items()}
        out["vento"][plano] = ventos
        phd = np.arange(0.0, phimax + 1e-9, dphi)
        GZ, alpha = curva_gz(x, KG, V0, plano, phd)
        phal = angulo_alagamento(x, V0, plano, phd, alpha)
        if phal > phd[-1]:                       # estende a curva até φal
            extra = np.arange(phd[-1] + dphi, phal + dphi + 1e-9, dphi)
            GZe, _ = curva_gz(x, KG, V0, plano, extra)
            phd, GZ = np.append(phd, extra), np.append(GZ, GZe)
        casos = {}
        for nome, (df, HM0, HMud, zclr) in ventos.items():
            ph = np.radians(phd)
            HA = (HM0 * np.cos(ph) + HMud * np.sin(ph)) / Dg
            c = criterio_areas(phd, GZ, HA, phal)
            c.update(HA=HA, HM0=HM0, HMud=HMud, HA0=HM0 / Dg, z_CLR=zclr)
            casos[nome] = c
            AB_min = min(AB_min, c["AB"])
            gzsen_min = min(gzsen_min, c["GZsen_min"])
        out[plano] = dict(phi=phd, GZ=GZ, phi_al=phal, casos=casos)
    out["AB_min"], out["GZsen_min"] = AB_min, gzsen_min
    return out
