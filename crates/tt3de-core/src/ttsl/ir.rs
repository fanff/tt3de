//! Post-SSA TTSL module dumped by the Python compiler for Cranelift.
//!
//! This is the CFG after `PassSSARenamer` and before phi lowering / VM
//! register allocation. Seeded shader inputs still name a VM register so the
//! host can write the same slots the interpreter uses.

use std::collections::HashMap;
use std::fmt;
use std::str::FromStr;

use serde::Deserialize;

pub const SSA_MODULE_VERSION: u32 = 1;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum IrTy {
    F32,
    I32,
    Bool,
    V2,
    V3,
    V4,
}

impl IrTy {
    pub fn width(self) -> usize {
        match self {
            IrTy::F32 | IrTy::I32 | IrTy::Bool => 1,
            IrTy::V2 => 2,
            IrTy::V3 => 3,
            IrTy::V4 => 4,
        }
    }

    pub fn is_float_lane(self) -> bool {
        !matches!(self, IrTy::I32 | IrTy::Bool)
    }
}

impl FromStr for IrTy {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "F32" => Ok(IrTy::F32),
            "I32" => Ok(IrTy::I32),
            "BOOL" => Ok(IrTy::Bool),
            "V2" => Ok(IrTy::V2),
            "V3" => Ok(IrTy::V3),
            "V4" => Ok(IrTy::V4),
            other => Err(format!("unknown IR type {other}")),
        }
    }
}

impl fmt::Display for IrTy {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            IrTy::F32 => "F32",
            IrTy::I32 => "I32",
            IrTy::Bool => "BOOL",
            IrTy::V2 => "V2",
            IrTy::V3 => "V3",
            IrTy::V4 => "V4",
        })
    }
}

#[derive(Clone, Debug, Deserialize)]
pub struct SsaInput {
    pub name: String,
    pub ty: IrTy,
    pub temp: u32,
    pub reg: Option<u32>,
}

#[derive(Clone, Debug, Deserialize)]
pub struct SsaConst {
    pub id: u32,
    pub ty: IrTy,
    pub value: Vec<f64>,
}

#[derive(Clone, Debug, Deserialize)]
pub struct SsaPhi {
    pub dst: u32,
    pub ty: IrTy,
    pub operands: Vec<(u32, u32)>,
}

impl SsaPhi {
    pub fn operand_from(&self, pred: u32) -> Option<u32> {
        self.operands
            .iter()
            .find_map(|(p, t)| (*p == pred).then_some(*t))
    }
}

#[derive(Clone, Debug, Deserialize)]
pub struct SsaInstr {
    pub op: String,
    #[serde(default)]
    pub ty: Option<IrTy>,
    #[serde(default)]
    pub dst: Option<u32>,
    #[serde(default)]
    pub src: Vec<u32>,
    #[serde(default)]
    pub imm: Option<u32>,
    #[serde(default)]
    pub target: Option<u32>,
    #[serde(default)]
    pub fallthrough: Option<u32>,
}

#[derive(Clone, Debug, Deserialize)]
pub struct SsaBlock {
    pub id: u32,
    pub name: String,
    #[serde(default)]
    pub phis: Vec<SsaPhi>,
    #[serde(default)]
    pub instrs: Vec<SsaInstr>,
}

#[derive(Clone, Debug, Deserialize)]
pub struct TtslSsaModule {
    pub version: u32,
    pub entry: u32,
    #[serde(default)]
    pub inputs: Vec<SsaInput>,
    #[serde(default)]
    pub temps: HashMap<String, IrTy>,
    #[serde(default)]
    pub consts: Vec<SsaConst>,
    pub blocks: Vec<SsaBlock>,
}

impl TtslSsaModule {
    pub fn from_json(text: &str) -> Result<Self, String> {
        let module: Self = serde_json::from_str(text).map_err(|err| format!("SSA JSON: {err}"))?;
        module.validate()?;
        Ok(module)
    }

    pub fn block(&self, id: u32) -> Option<&SsaBlock> {
        self.blocks.iter().find(|b| b.id == id)
    }

    pub fn temp_ty(&self, temp: u32) -> Option<IrTy> {
        self.temps.get(&temp.to_string()).copied()
    }

    fn validate(&self) -> Result<(), String> {
        if self.version != SSA_MODULE_VERSION {
            return Err(format!(
                "unsupported SSA module version {} (expected {SSA_MODULE_VERSION})",
                self.version
            ));
        }
        if self.block(self.entry).is_none() {
            return Err(format!("entry block {} is missing", self.entry));
        }
        for block in &self.blocks {
            let last = block.instrs.last().ok_or_else(|| {
                format!("block {} ({}) has no instructions", block.id, block.name)
            })?;
            if !matches!(last.op.as_str(), "jmp" | "jmp_if_false" | "ret") {
                return Err(format!(
                    "block {} ({}) is missing a terminator",
                    block.id, block.name
                ));
            }
        }
        Ok(())
    }

    /// Identity shader: return the V4/V4/I32 values already sitting in `Registers`.
    pub fn passthrough_ret(front_reg: u32, back_reg: u32, glyph_reg: u32) -> Self {
        let mut temps = HashMap::new();
        temps.insert("1".into(), IrTy::V4);
        temps.insert("2".into(), IrTy::V4);
        temps.insert("3".into(), IrTy::I32);
        Self {
            version: SSA_MODULE_VERSION,
            entry: 0,
            inputs: vec![
                SsaInput {
                    name: "front".into(),
                    ty: IrTy::V4,
                    temp: 1,
                    reg: Some(front_reg),
                },
                SsaInput {
                    name: "back".into(),
                    ty: IrTy::V4,
                    temp: 2,
                    reg: Some(back_reg),
                },
                SsaInput {
                    name: "glyph".into(),
                    ty: IrTy::I32,
                    temp: 3,
                    reg: Some(glyph_reg),
                },
            ],
            temps,
            consts: vec![],
            blocks: vec![SsaBlock {
                id: 0,
                name: "_INIT_".into(),
                phis: vec![],
                instrs: vec![SsaInstr {
                    op: "ret".into(),
                    ty: None,
                    dst: None,
                    src: vec![1, 2, 3],
                    imm: None,
                    target: None,
                    fallthrough: None,
                }],
            }],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_minimal_module() {
        let json = r#"{
            "version": 1,
            "entry": 0,
            "inputs": [{"name": "tt_Time", "ty": "F32", "temp": 1, "reg": 3}],
            "temps": {"1": "F32", "2": "F32"},
            "consts": [{"id": 0, "ty": "F32", "value": [2.0]}],
            "blocks": [{
                "id": 0,
                "name": "_INIT_",
                "phis": [],
                "instrs": [
                    {"op": "load_const", "ty": "F32", "dst": 2, "imm": 0},
                    {"op": "ret", "src": [2, 2, 2]}
                ]
            }]
        }"#;
        let module = TtslSsaModule::from_json(json).unwrap();
        assert_eq!(module.entry, 0);
        assert_eq!(module.inputs[0].reg, Some(3));
        assert_eq!(module.temp_ty(1), Some(IrTy::F32));
        assert_eq!(module.blocks[0].instrs[0].op, "load_const");
    }

    #[test]
    fn passthrough_ret_validates() {
        let module = TtslSsaModule::passthrough_ret(0, 1, 9);
        module.validate().unwrap();
        assert_eq!(module.inputs[2].reg, Some(9));
        assert_eq!(module.blocks[0].instrs[0].op, "ret");
    }
}
