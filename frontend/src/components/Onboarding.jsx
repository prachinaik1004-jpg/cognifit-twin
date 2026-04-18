import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const activityLevels = [
  { id: 'sedentary', label: 'Sedentary', description: 'Little to no exercise' },
  { id: 'lightly', label: 'Lightly Active', description: 'Light exercise 1-3 days/week' },
  { id: 'moderately', label: 'Moderately Active', description: 'Moderate exercise 3-5 days/week' },
  { id: 'very', label: 'Very Active', description: 'Hard exercise 6-7 days/week' },
];

export default function Onboarding({ onComplete, onBack }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    sex: '',
    height: '',
    weight: '',
    smoking: '',
    drinking: '',
    activityLevel: '',
    cycleRegularity: '',
    hormonalConditions: '',
    hormonalConditionDetails: '',
  });

  const handleNext = () => {
    if (step < 4) {
      setStep(step + 1);
    } else {
      onComplete(formData);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    } else {
      onBack();
    }
  };

  const updateField = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const isStepValid = () => {
    switch (step) {
      case 1:
        return formData.name && formData.age && formData.sex && formData.height && formData.weight;
      case 2:
        return formData.smoking && formData.drinking && formData.activityLevel;
      case 3:
        if (formData.sex === 'female') {
          return formData.cycleRegularity && formData.hormonalConditions;
        }
        return true;
      case 4:
        return true;
      default:
        return false;
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-teal-50/30 overflow-y-auto relative">
      {/* Decorative elements */}
      <motion.div
        animate={{ y: [0, -20, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-20 left-20 w-48 h-48 bg-primary/5 rounded-full blur-3xl"
      />
      <motion.div
        animate={{ y: [0, 20, 0] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-20 right-20 w-64 h-64 bg-teal-500/5 rounded-full blur-3xl"
      />

      <div className="relative z-10 max-w-2xl mx-auto px-6 w-full py-8">
        {/* Progress Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg shadow-gray-200/50 p-6 mb-8 border border-gray-100"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-text-main">
              Step {step} of 4
            </span>
            <span className="text-sm font-semibold text-primary">
              {Math.round((step / 4) * 100)}%
            </span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-primary to-teal-600 rounded-full"
              initial={{ width: '25%' }}
              animate={{ width: `${(step / 4) * 100}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          </div>
        </motion.div>

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="bg-white rounded-2xl shadow-xl shadow-gray-200/50 p-8 border border-gray-100"
          >
            {step === 1 && (
              <Step1
                formData={formData}
                updateField={updateField}
                onNext={handleNext}
                onBack={handleBack}
              />
            )}
            {step === 2 && (
              <Step2
                formData={formData}
                updateField={updateField}
                onNext={handleNext}
                onBack={handleBack}
              />
            )}
            {step === 3 && (
              <Step3
                formData={formData}
                updateField={updateField}
                onNext={handleNext}
                onBack={handleBack}
              />
            )}
            {step === 4 && (
              <Step4
                formData={formData}
                onComplete={onComplete}
                onBack={handleBack}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

function Step1({ formData, updateField, onNext, onBack }) {
  return (
    <>
      <h2 className="font-serif text-3xl text-text-main mb-2">Basic Demographics</h2>
      <p className="text-sm text-text-muted mb-8">
        Let's get to know you better
      </p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-semibold text-text-main mb-2">
            Full Name
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => updateField('name', e.target.value)}
            placeholder="Enter your name"
            className="w-full px-4 py-4 rounded-xl border-2 border-gray-200 focus:border-primary focus:outline-none transition-colors bg-gray-50 focus:bg-white"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-text-main mb-2">
              Age
            </label>
            <input
              type="number"
              value={formData.age}
              onChange={(e) => updateField('age', e.target.value)}
              placeholder="25"
              className="w-full px-4 py-4 rounded-xl border-2 border-gray-200 focus:border-primary focus:outline-none transition-colors bg-gray-50 focus:bg-white"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-text-main mb-2">
              Sex
            </label>
            <select
              value={formData.sex}
              onChange={(e) => updateField('sex', e.target.value)}
              className="w-full px-4 py-4 rounded-xl border-2 border-gray-200 focus:border-primary focus:outline-none transition-colors bg-gray-50 focus:bg-white"
            >
              <option value="">Select</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-text-main mb-2">
              Height (cm)
            </label>
            <input
              type="number"
              value={formData.height}
              onChange={(e) => updateField('height', e.target.value)}
              placeholder="170"
              className="w-full px-4 py-4 rounded-xl border-2 border-gray-200 focus:border-primary focus:outline-none transition-colors bg-gray-50 focus:bg-white"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-text-main mb-2">
              Weight (kg)
            </label>
            <input
              type="number"
              value={formData.weight}
              onChange={(e) => updateField('weight', e.target.value)}
              placeholder="70"
              className="w-full px-4 py-4 rounded-xl border-2 border-gray-200 focus:border-primary focus:outline-none transition-colors bg-gray-50 focus:bg-white"
            />
          </div>
        </div>
      </div>

      <div className="flex gap-4 mt-8">
        <button
          onClick={onBack}
          className="px-6 py-4 rounded-xl border-2 border-gray-200 text-text-main font-semibold hover:border-gray-300 hover:bg-gray-50 transition-all cursor-pointer"
        >
          Back
        </button>
        <button
          onClick={onNext}
          disabled={!formData.name || !formData.age || !formData.sex || !formData.height || !formData.weight}
          className="flex-1 px-6 py-4 rounded-xl bg-gradient-to-r from-primary to-teal-600 text-white font-semibold hover:shadow-lg hover:shadow-primary/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer"
        >
          Continue
        </button>
      </div>
    </>
  );
}

function Step2({ formData, updateField, onNext, onBack }) {
  return (
    <>
      <h2 className="font-serif text-3xl text-text-main mb-2">Lifestyle</h2>
      <p className="text-sm text-text-muted mb-8">
        Help us understand your daily habits
      </p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-semibold text-text-main mb-3">
            Do you smoke?
          </label>
          <div className="flex gap-3">
            {['No', 'Occasionally', 'Yes'].map((option) => (
              <button
                key={option}
                onClick={() => updateField('smoking', option)}
                className={`flex-1 px-4 py-4 rounded-xl border-2 transition-all cursor-pointer ${
                  formData.smoking === option
                    ? 'border-primary bg-primary/10 text-primary font-semibold'
                    : 'border-gray-200 hover:border-gray-300 bg-gray-50 hover:bg-white'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-text-main mb-3">
            Do you drink alcohol?
          </label>
          <div className="flex gap-3">
            {['No', 'Occasionally', 'Yes'].map((option) => (
              <button
                key={option}
                onClick={() => updateField('drinking', option)}
                className={`flex-1 px-4 py-4 rounded-xl border-2 transition-all cursor-pointer ${
                  formData.drinking === option
                    ? 'border-primary bg-primary/10 text-primary font-semibold'
                    : 'border-gray-200 hover:border-gray-300 bg-gray-50 hover:bg-white'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-text-main mb-3">
            Activity Level
          </label>
          <div className="space-y-3">
            {activityLevels.map((level) => (
              <button
                key={level.id}
                onClick={() => updateField('activityLevel', level.id)}
                className={`w-full px-5 py-4 rounded-xl border-2 text-left transition-all cursor-pointer ${
                  formData.activityLevel === level.id
                    ? 'border-primary bg-primary/10 text-primary font-semibold'
                    : 'border-gray-200 hover:border-gray-300 bg-gray-50 hover:bg-white'
                }`}
              >
                <div className="font-medium text-sm">{level.label}</div>
                <div className="text-xs text-text-muted mt-1">{level.description}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex gap-4 mt-8">
        <button
          onClick={onBack}
          className="px-6 py-4 rounded-xl border-2 border-gray-200 text-text-main font-semibold hover:border-gray-300 hover:bg-gray-50 transition-all cursor-pointer"
        >
          Back
        </button>
        <button
          onClick={onNext}
          disabled={!formData.smoking || !formData.drinking || !formData.activityLevel}
          className="flex-1 px-6 py-4 rounded-xl bg-gradient-to-r from-primary to-teal-600 text-white font-semibold hover:shadow-lg hover:shadow-primary/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer"
        >
          Continue
        </button>
      </div>
    </>
  );
}

function Step3({ formData, updateField, onNext, onBack }) {
  if (formData.sex !== 'female') {
    return (
      <>
        <h2 className="font-serif text-3xl text-text-main mb-2">Health History</h2>
        <p className="text-sm text-text-muted mb-8">
          This section is not applicable for your profile
        </p>

        <div className="flex gap-4 mt-8">
          <button
            onClick={onBack}
            className="px-6 py-4 rounded-xl border-2 border-gray-200 text-text-main font-semibold hover:border-gray-300 hover:bg-gray-50 transition-all cursor-pointer"
          >
            Back
          </button>
          <button
            onClick={onNext}
            className="flex-1 px-6 py-4 rounded-xl bg-gradient-to-r from-primary to-teal-600 text-white font-semibold hover:shadow-lg hover:shadow-primary/30 transition-all cursor-pointer"
          >
            Continue
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      <h2 className="font-serif text-3xl text-text-main mb-2">Women's Health</h2>
      <p className="text-sm text-text-muted mb-8">
        Help us provide personalized insights
      </p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-semibold text-text-main mb-3">
            Cycle Regularity
          </label>
          <div className="flex gap-3">
            {['Regular', 'Irregular', 'Not Applicable'].map((option) => (
              <button
                key={option}
                onClick={() => updateField('cycleRegularity', option)}
                className={`flex-1 px-4 py-4 rounded-xl border-2 transition-all cursor-pointer ${
                  formData.cycleRegularity === option
                    ? 'border-primary bg-primary/10 text-primary font-semibold'
                    : 'border-gray-200 hover:border-gray-300 bg-gray-50 hover:bg-white'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-text-main mb-3">
            Any hormonal conditions? (PCOS, thyroid, etc.)
          </label>
          <div className="flex gap-3 mb-4">
            {['No', 'Yes'].map((option) => (
              <button
                key={option}
                onClick={() => updateField('hormonalConditions', option)}
                className={`flex-1 px-4 py-4 rounded-xl border-2 transition-all cursor-pointer ${
                  formData.hormonalConditions === option
                    ? 'border-primary bg-primary/10 text-primary font-semibold'
                    : 'border-gray-200 hover:border-gray-300 bg-gray-50 hover:bg-white'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
          {formData.hormonalConditions === 'Yes' && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              transition={{ duration: 0.3 }}
            >
              <label className="block text-sm font-semibold text-text-main mb-2">
                Please specify your condition
              </label>
              <input
                type="text"
                value={formData.hormonalConditionDetails}
                onChange={(e) => updateField('hormonalConditionDetails', e.target.value)}
                placeholder="e.g., PCOS, Hypothyroidism, etc."
                className="w-full px-4 py-4 rounded-xl border-2 border-gray-200 focus:border-primary focus:outline-none transition-colors bg-gray-50 focus:bg-white"
              />
            </motion.div>
          )}
        </div>
      </div>

      <div className="flex gap-4 mt-8">
        <button
          onClick={onBack}
          className="px-6 py-4 rounded-xl border-2 border-gray-200 text-text-main font-semibold hover:border-gray-300 hover:bg-gray-50 transition-all cursor-pointer"
        >
          Back
        </button>
        <button
          onClick={onNext}
          disabled={
            !formData.cycleRegularity ||
            !formData.hormonalConditions ||
            (formData.hormonalConditions === 'Yes' && !formData.hormonalConditionDetails)
          }
          className="flex-1 px-6 py-4 rounded-xl bg-gradient-to-r from-primary to-teal-600 text-white font-semibold hover:shadow-lg hover:shadow-primary/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer"
        >
          Continue
        </button>
      </div>
    </>
  );
}

function Step4({ formData, onComplete, onBack }) {
  return (
    <>
      <h2 className="font-serif text-3xl text-text-main mb-2">Review & Confirm</h2>
      <p className="text-sm text-text-muted mb-8">
        Please review your information before proceeding
      </p>

      <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-6 border border-gray-100 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <label className="text-xs text-text-muted uppercase tracking-wider">Name</label>
            <p className="text-text-main font-semibold mt-1">{formData.name}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <label className="text-xs text-text-muted uppercase tracking-wider">Age</label>
            <p className="text-text-main font-semibold mt-1">{formData.age} years</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <label className="text-xs text-text-muted uppercase tracking-wider">Sex</label>
            <p className="text-text-main font-semibold mt-1 capitalize">{formData.sex}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <label className="text-xs text-text-muted uppercase tracking-wider">Height / Weight</label>
            <p className="text-text-main font-semibold mt-1">
              {formData.height} cm / {formData.weight} kg
            </p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <label className="text-xs text-text-muted uppercase tracking-wider">Smoking</label>
            <p className="text-text-main font-semibold mt-1">{formData.smoking}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <label className="text-xs text-text-muted uppercase tracking-wider">Drinking</label>
            <p className="text-text-main font-semibold mt-1">{formData.drinking}</p>
          </div>
          <div className="col-span-2 bg-white rounded-xl p-4 border border-gray-100">
            <label className="text-xs text-text-muted uppercase tracking-wider">Activity Level</label>
            <p className="text-text-main font-semibold mt-1">
              {activityLevels.find((l) => l.id === formData.activityLevel)?.label}
            </p>
          </div>
          {formData.sex === 'female' && (
            <>
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <label className="text-xs text-text-muted uppercase tracking-wider">Cycle Regularity</label>
                <p className="text-text-main font-semibold mt-1">{formData.cycleRegularity}</p>
              </div>
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <label className="text-xs text-text-muted uppercase tracking-wider">Hormonal Conditions</label>
                <p className="text-text-main font-semibold mt-1">{formData.hormonalConditions}</p>
                {formData.hormonalConditions === 'Yes' && formData.hormonalConditionDetails && (
                  <p className="text-xs text-text-muted mt-1">{formData.hormonalConditionDetails}</p>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      <div className="flex gap-4 mt-8">
        <button
          onClick={onBack}
          className="px-6 py-4 rounded-xl border-2 border-gray-200 text-text-main font-semibold hover:border-gray-300 hover:bg-gray-50 transition-all cursor-pointer"
        >
          Back
        </button>
        <button
          onClick={() => onComplete(formData)}
          className="flex-1 px-6 py-4 rounded-xl bg-gradient-to-r from-primary to-teal-600 text-white font-semibold hover:shadow-lg hover:shadow-primary/30 transition-all cursor-pointer"
        >
          Complete Onboarding
        </button>
      </div>
    </>
  );
}
