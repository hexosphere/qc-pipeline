<p align="center">
  <a href="">
    <img src="https://www.tronntech.com/wp-content/uploads/2019/06/Quantum_Physics_featured.jpg" alt="Logo" width=160 height=107>
  </a>

  <h3 align="center">CHAINS</h3>

  <p align="center">
    Short description
    <br>
    <a href="https://github.com/hexosphere/qc-pipeline/issues/new?template=bug.md">Report bug</a>
    ·
    <a href="https://github.com/hexosphere/qc-pipeline/issues/new?template=feature.md&labels=feature">Request feature</a>
  </p>
</p>

## Table of contents

- [Table of contents](#table-of-contents)
- [Quick start](#quick-start)
  - [CHAINS dir tree](#chains-dir-tree)
  - [CECIHOME dir tree](#cecihome-dir-tree)
- [External resources](#external-resources)

## Quick start

### Workflow

<p align="center">
  <a href="">
    <img src="Documentation\chains_workflow.png" alt="workflow_image" width=775 height=559>
  </a>
</p>

### CHAINS dir tree

```text
└── abin_launcher/
      └── Templates/
            ├── orca_job.sh.jinja
            ├── orca.inp.jinja
            ├── qchem_job.sh.jinja
            └── qchem.in.jinja
      ├── abin_launcher.py
      ├── mol_scan.py
      ├── scaling_fcts.py
      ├── renderer.py
      ├── elements.yml
      ├── config.yml
      └── clusters.yml
└── control_launcher/
      └── Templates/
            ├── jinja-template1
            ├── jinja-template2
            └── etc.
      ├── qchem_parser.py
      └── control_launcher.py
└── results_treatment/
      ├── some jinja LaTeX templates for the tables
      └── some gnuplots scripts for the graphs
└── crontab_scripts/
      ├── orca2qchem.sh
      ├── qchem2control.sh
      └── control2results.sh
└── check_scripts/
      ├── orca_check.py
      └── qchem_check.py
├── load_modules.sh
└── readme.md
```

### CECIHOME dir tree

```text
└── CHAINS (see above)
└── STARTING
     ├── molecule1.xyz
     ├── molecule2.xyz
     └── etc.
└── ORCA_OUT
     ├── molecule1_opt.xyz
     ├── molecule2_opt.xyz
     └── etc.
└── Q-CHEM_OUT
     ├── molecule1.out
     ├── molecule2.out
     └── etc.
└── CONTROL_OUT
     ├── molecule1/
     ├── molecule2/
     └── etc.
└── FINAL
     └── molecule1/
            ├── ORCA
            ├── Q-CHEM
            ├── CONTROL
            ├── RESULTS
            └── molecule1_config.yml
     └── molecule2/
            ├── ORCA
            ├── Q-CHEM
            ├── CONTROL
            ├── RESULTS
            └── molecule2_config.yml
     └── etc.
```

## External resources

- Project readme template in markdown: https://github.com/Ismaestro/markdown-template
- Project image: https://www.tronntech.com/2019/07/19/quantum-computers/

