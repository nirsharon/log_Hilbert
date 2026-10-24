import Mathlib

/-!
Partial formalization of the algebraic core of the log-Hilbert manuscript.

This file does not formalize Sobolev composition, matrix/Riemannian distance
comparisons, RKHS construction, or the analytic multilevel estimates.
The chart is an actual bijection. Operators in the conjugacy result can be
nonlinear. The telescoping theorem is separately proved for linear projections,
and instantiated with mathlib's orthogonal projections onto nested subspaces.

Indices: Q 0 is the paper's first-level operator; iterate Q b (n+1) corresponds
to the paper's approximation after n+1 levels.
-/

set_option autoImplicit false

namespace LogHilbert

section Transport

variable {G H D : Type*}

/-- Transport any map through the logarithmic chart. -/
def lift (e : G ≃ H) (A : H → H) (g : G) : G := e.symm (A (e g))

@[simp] theorem chart_lift (e : G ≃ H) (A : H → H) (g : G) :
    e (lift e A g) = A (e g) := by
  simp [lift]

/-- Pointwise chart on function spaces. Membership in analytic function spaces
must be checked separately; no such membership is silently assumed here. -/
def functionChart (e : G ≃ H) : (D → G) ≃ (D → H) where
  toFun F x := e (F x)
  invFun B x := e.symm (B x)
  left_inv F := by funext x; exact e.symm_apply_apply (F x)
  right_inv B := by funext x; exact e.apply_symm_apply (B x)

@[simp] theorem functionChart_apply (e : G ≃ H) (F : D → G) (x : D) :
    functionChart e F x = e (F x) := rfl

theorem lift_composition (e : G ≃ H) (A B : H → H) :
    lift e (A ∘ B) = lift e A ∘ lift e B := by
  funext g
  simp [lift]

theorem lift_idempotent (e : G ≃ H) (A : H → H)
    (hA : ∀ x, A (A x) = A x) : ∀ g, lift e A (lift e A g) = lift e A g := by
  intro g
  simp only [lift, Equiv.apply_symm_apply]
  rw [hA]

variable [AddCommGroup H]

def transportedAdd (e : G ≃ H) (g h : G) : G := e.symm (e g + e h)
def transportedSub (e : G ≃ H) (g h : G) : G := e.symm (e g - e h)
def transportedZero (e : G ≃ H) : G := e.symm 0

@[simp] theorem chart_add (e : G ≃ H) (g h : G) :
    e (transportedAdd e g h) = e g + e h := by simp [transportedAdd]

@[simp] theorem chart_sub (e : G ≃ H) (g h : G) :
    e (transportedSub e g h) = e g - e h := by simp [transportedSub]

@[simp] theorem chart_zero (e : G ≃ H) :
    e (transportedZero e) = 0 := by simp [transportedZero]

theorem transportedAdd_assoc (e : G ≃ H) (g h k : G) :
    transportedAdd e (transportedAdd e g h) k =
      transportedAdd e g (transportedAdd e h k) := by
  apply e.injective
  simp [add_assoc]

theorem transportedAdd_comm (e : G ≃ H) (g h : G) :
    transportedAdd e g h = transportedAdd e h g := by
  apply e.injective
  simp [add_comm]

theorem transportedAdd_zero (e : G ≃ H) (g : G) :
    transportedAdd e g (transportedZero e) = g := by
  apply e.injective
  simp

/-- Proposition 3.1's discrepancy identity. N may be any functional; taking it
to be a function-space norm gives exactly the paper's algebraic identity. -/
theorem transference (e : G ≃ H) (N : H → ℝ) (A : H → H) (g : G) :
    N (e g - e (lift e A g)) = N (e g - A (e g)) := by
  simp

end Transport

section Metric

variable {G H : Type*} [NormedAddCommGroup H]

/-- Metric pulled back by the actual chart, using mathlib's induced metric. -/
def pulledMetric (e : G ≃ H) : MetricSpace G :=
  MetricSpace.induced e e.injective inferInstance

def chartIsometry (e : G ≃ H) :
    letI : MetricSpace G := pulledMetric e
    G ≃ᵢ H := by
  letI : MetricSpace G := pulledMetric e
  exact { e with isometry_toFun := by intro g h; rfl }

theorem pulledMetric_complete [CompleteSpace H] (e : G ≃ H) :
    letI : MetricSpace G := pulledMetric e
    CompleteSpace G := by
  letI : MetricSpace G := pulledMetric e
  exact (chartIsometry e).completeSpace

theorem chart_distance (e : G ≃ H) (g h : G) :
    letI : MetricSpace G := pulledMetric e
    dist g h = ‖e g - e h‖ := by
  change dist (e g) (e h) = _
  exact dist_eq_norm _ _

end Metric

section HilbertStructure

variable {G H : Type*} [NormedAddCommGroup H] [InnerProductSpace ℝ H]

/-- Proposition 2.5: the transported additive group and norm. -/
abbrev chartNormedGroup (e : G ≃ H) : NormedAddCommGroup G := by
  letI : AddCommGroup G := e.addCommGroup
  exact NormedAddCommGroup.induced G H e.addEquiv e.injective

abbrev chartModule (e : G ≃ H) :
    letI : NormedAddCommGroup G := chartNormedGroup e
    Module ℝ G := by
  letI : NormedAddCommGroup G := chartNormedGroup e
  exact e.module ℝ

/-- Pull back the actual inner product, retaining the induced norm. -/
noncomputable def chartInnerProductSpace (e : G ≃ H) :
    letI : NormedAddCommGroup G := chartNormedGroup e
    letI : Module ℝ G := chartModule e
    InnerProductSpace ℝ G := by
  letI : NormedAddCommGroup G := chartNormedGroup e
  letI : Module ℝ G := chartModule e
  let L : G ≃ₗ[ℝ] H := Equiv.linearEquiv ℝ e
  exact {
    NormedSpace.induced ℝ G H L with
    inner := fun x y => @inner ℝ H _ (L x) (L y)
    norm_sq_eq_re_inner := fun x => norm_sq_eq_re_inner (L x)
    conj_inner_symm := fun x y => by
      change @inner ℝ H _ (L y) (L x) = @inner ℝ H _ (L x) (L y)
      exact real_inner_comm _ _
    add_left := fun x y z => by simp only [L.map_add, inner_add_left]
    smul_left := fun x y r => by simp only [L.map_smul, inner_smul_left]
  }

/-- The logarithmic chart is a linear isometric equivalence; its inverse is
the paper's exponential linear isometry. -/
noncomputable def chartLinearIsometry (e : G ≃ H) :
    letI : NormedAddCommGroup G := chartNormedGroup e
    letI : Module ℝ G := chartModule e
    letI : InnerProductSpace ℝ G := chartInnerProductSpace e
    G ≃ₗᵢ[ℝ] H := by
  letI : NormedAddCommGroup G := chartNormedGroup e
  letI : Module ℝ G := chartModule e
  letI : InnerProductSpace ℝ G := chartInnerProductSpace e
  exact { Equiv.linearEquiv ℝ e with norm_map' := fun _ => rfl }

/-- Completeness of the transported inner product space, completing the
abstract Hilbert-space assertion in Proposition 2.5. -/
theorem transportedHilbert_complete [CompleteSpace H] (e : G ≃ H) :
    letI : NormedAddCommGroup G := chartNormedGroup e
    letI : Module ℝ G := chartModule e
    letI : InnerProductSpace ℝ G := chartInnerProductSpace e
    CompleteSpace G := by
  letI : NormedAddCommGroup G := chartNormedGroup e
  letI : Module ℝ G := chartModule e
  letI : InnerProductSpace ℝ G := chartInnerProductSpace e
  exact (chartLinearIsometry e).toIsometryEquiv.completeSpace

omit [InnerProductSpace ℝ H] in
theorem transference_norm (e : G ≃ H) (A : H → H) (g : G) :
    letI : NormedAddCommGroup G := chartNormedGroup e
    ‖transportedSub e g (lift e A g)‖ = ‖e g - A (e g)‖ := by
  letI : NormedAddCommGroup G := chartNormedGroup e
  change ‖e (transportedSub e g (lift e A g))‖ = _
  simp

omit [InnerProductSpace ℝ H] in
theorem lift_norm_bound (e : G ≃ H) (A : H → H) (C : ℝ)
    (bound : ∀ b, ‖A b‖ ≤ C * ‖b‖) :
    letI : NormedAddCommGroup G := chartNormedGroup e
    ∀ g, ‖lift e A g‖ ≤ C * ‖g‖ := by
  letI : NormedAddCommGroup G := chartNormedGroup e
  intro g
  change ‖e (lift e A g)‖ ≤ C * ‖e g‖
  simpa using bound (e g)

end HilbertStructure

section TransportedLinearity

variable {G H : Type*} [AddCommGroup H] [Module ℝ H]

/-- Proposition 3.1's inheritance of linearity. No inner-product or norm
assumption is required, so this also covers the paper's non-Hilbertian
function spaces whenever they are real vector spaces. -/
noncomputable def liftLinear (e : G ≃ H) (A : H →ₗ[ℝ] H) :
    letI : AddCommGroup G := e.addCommGroup
    letI : Module ℝ G := e.module ℝ
    G →ₗ[ℝ] G := by
  letI : AddCommGroup G := e.addCommGroup
  letI : Module ℝ G := e.module ℝ
  let E : G ≃ₗ[ℝ] H := Equiv.linearEquiv ℝ e
  exact E.symm.toLinearMap.comp (A.comp E.toLinearMap)

theorem liftLinear_apply (e : G ≃ H) (A : H →ₗ[ℝ] H) (g : G) :
    letI : AddCommGroup G := e.addCommGroup
    letI : Module ℝ G := e.module ℝ
    liftLinear e A g = lift e A g := rfl

end TransportedLinearity

section Conjugacy

variable {G H : Type*} [AddCommGroup H]

/-- Residual-correction algorithm in the additive model space. -/
def iterate (Q : ℕ → H → H) (b : H) : ℕ → H
  | 0 => 0
  | n + 1 => iterate Q b n + Q n (b - iterate Q b n)

/-- The algorithm expressed using the transported operations on G. -/
def transportedIterate (e : G ≃ H) (Q : ℕ → H → H) (g : G) : ℕ → G
  | 0 => transportedZero e
  | n + 1 => transportedAdd e (transportedIterate e Q g n)
      (lift e (Q n) (transportedSub e g (transportedIterate e Q g n)))

/-- Proposition 5.1: level-by-level conjugacy, without linearity assumptions. -/
theorem iterate_conjugacy (e : G ≃ H) (Q : ℕ → H → H) (g : G) (n : ℕ) :
    e (transportedIterate e Q g n) = iterate Q (e g) n := by
  induction n with
  | zero => simp [transportedIterate, iterate]
  | succ n ih => simp [transportedIterate, iterate, ih]

theorem residual_conjugacy (e : G ≃ H) (Q : ℕ → H → H) (g : G) (n : ℕ) :
    e (transportedSub e g (transportedIterate e Q g n)) =
      e g - iterate Q (e g) n := by
  simp [iterate_conjugacy]

theorem correction_conjugacy (e : G ≃ H) (Q : ℕ → H → H) (g : G) (n : ℕ) :
    e (lift e (Q n) (transportedSub e g (transportedIterate e Q g n))) =
      Q n (e g - iterate Q (e g) n) := by
  simp [iterate_conjugacy]

/-- The commutative diagram as an equality of maps. -/
theorem commuting_diagram (e : G ≃ H) (Q : ℕ → H → H) (n : ℕ) :
    (fun g => transportedIterate e Q g n) =
      e.symm ∘ (fun b => iterate Q b n) ∘ e := by
  funext g
  apply e.injective
  simp [iterate_conjugacy]

end Conjugacy

section LinearAlgorithms

variable {H : Type*} [AddCommGroup H] [Module ℝ H]

/-- Ordered residual operators: the newest factor acts on the left. -/
def residualOperator (P : ℕ → H →ₗ[ℝ] H) : ℕ → H →ₗ[ℝ] H
  | 0 => LinearMap.id
  | n + 1 => (LinearMap.id - P n).comp (residualOperator P n)

theorem residual_operator_identity (P : ℕ → H →ₗ[ℝ] H) (b : H) (n : ℕ) :
    b - iterate (fun j => P j) b n = residualOperator P n b := by
  induction n with
  | zero => simp [iterate, residualOperator]
  | succ n ih =>
    simp only [iterate, residualOperator, LinearMap.comp_apply,
      LinearMap.sub_apply, LinearMap.id_apply, ← ih]
    abel

/-- Telescoping needs nested projection absorption, rather than commutation
of arbitrary level-dependent approximation operators. -/
theorem telescoping (P : ℕ → H →ₗ[ℝ] H)
    (nested : ∀ n x, P (n + 1) (P n x) = P n x) (b : H) (n : ℕ) :
    iterate (fun j => P j) b (n + 1) = P n b := by
  induction n with
  | zero => simp [iterate]
  | succ n ih =>
    change iterate (fun j => P j) b (n + 1) +
      P (n + 1) (b - iterate (fun j => P j) b (n + 1)) = P (n + 1) b
    rw [ih, map_sub, nested]
    abel

end LinearAlgorithms

section OrthogonalProjections

variable {H : Type*} [NormedAddCommGroup H] [InnerProductSpace ℝ H]

/-- Ambient-valued version of mathlib's subspace-valued projection. -/
noncomputable def ambientProjection (V : Submodule ℝ H)
    [V.HasOrthogonalProjection] : H →ₗ[ℝ] H :=
  V.subtype.comp V.orthogonalProjection.toLinearMap

theorem nested_projection_absorption (V W : Submodule ℝ H)
    [V.HasOrthogonalProjection] [W.HasOrthogonalProjection]
    (hVW : V ≤ W) (b : H) :
    ambientProjection W (ambientProjection V b) = ambientProjection V b := by
  change (W.orthogonalProjection (ambientProjection V b) : H) = _
  apply (Submodule.orthogonalProjection_eq_self_iff).2
  exact hVW (V.orthogonalProjection b).property

/-- Theorem 5.2's Hilbert-space telescoping assertion, instantiated with genuine
orthogonal projections. The RKHS/kernel identification is a separate task. -/
theorem orthogonal_telescoping (V : ℕ → Submodule ℝ H)
    [∀ n, (V n).HasOrthogonalProjection]
    (nested : ∀ n, V n ≤ V (n + 1)) (b : H) (n : ℕ) :
    iterate (fun j => ambientProjection (V j)) b (n + 1) =
      ambientProjection (V n) b := by
  apply telescoping
  intro j x
  exact nested_projection_absorption (V j) (V (j + 1)) (nested j) x

end OrthogonalProjections

section Interpolation

variable {D H : Type*} [AddCommGroup H]

/-- Exact interpolation at the current sites forces the updated residual to
vanish there, independently of whether earlier site sets were nested. -/
theorem updated_residual_zero (b a : D → H) (Q : (D → H) → D → H)
    (X : Set D) (interpolates : ∀ u x, x ∈ X → Q u x = u x)
    (x : D) (hx : x ∈ X) :
    b x - (a x + Q (b - a) x) = 0 := by
  rw [interpolates (b - a) x hx]
  change b x - (a x + (b x - a x)) = 0
  abel

end Interpolation

section ScalarEstimates

/-- Conditional recurrence estimate. This checks the induction once the
analytic one-step bounds have been supplied; it does not prove those bounds. -/
theorem geometric_recurrence (a : ℕ → ℝ) (c : ℝ) (hc : 0 ≤ c)
    (step : ∀ n, a (n + 1) ≤ c * a n) (n : ℕ) :
    a n ≤ c ^ n * a 0 := by
  induction n with
  | zero => simp
  | succ n ih =>
    calc
      a (n + 1) ≤ c * a n := step n
      _ ≤ c * (c ^ n * a 0) := mul_le_mul_of_nonneg_left ih hc
      _ = c ^ (n + 1) * a 0 := by rw [pow_succ]; ring

/-- Actual convergence of the nonnegative scalar recurrence. The analytic
error sequences must still be shown to satisfy its hypotheses. -/
theorem geometric_recurrence_tendsto (a : ℕ → ℝ) (c : ℝ)
    (hc : 0 ≤ c) (hc1 : c < 1) (ha : ∀ n, 0 ≤ a n)
    (step : ∀ n, a (n + 1) ≤ c * a n) :
    Filter.Tendsto a Filter.atTop (nhds 0) := by
  apply squeeze_zero ha (geometric_recurrence a c hc step)
  simpa using (tendsto_pow_atTop_nhds_zero_of_lt_one hc hc1).mul_const (a 0)

end ScalarEstimates

section AffineEquivariance

variable {ι H : Type*} [Fintype ι] [AddCommGroup H] [Module ℝ H]

/-- The affine equivariance identity behind the revised invariant discussion.
It uses a linear map and constant reproduction (weights sum to one). -/
theorem weighted_affine_equivariance (w : ι → ℝ) (x : ι → H)
    (L : H →ₗ[ℝ] H) (a : H) (hw : ∑ i, w i = 1) :
    (∑ i, w i • (a + L (x i))) = a + L (∑ i, w i • x i) := by
  simp_rw [smul_add]
  rw [Finset.sum_add_distrib, ← Finset.sum_smul, hw, one_smul]
  congr 1
  simp

end AffineEquivariance

section BoundaryCheck

/-- An open ball of radius zero contains no possible minimizer. This is the
boundary clarification needed in the paper's Karcher statements. -/
theorem no_minimizer_at_zero_radius {M : Type*} [PseudoMetricSpace M] (p : M) :
    ¬ ∃ m : M, m ∈ Metric.ball p (2 * (0 : ℝ)) := by
  simp

end BoundaryCheck

end LogHilbert
