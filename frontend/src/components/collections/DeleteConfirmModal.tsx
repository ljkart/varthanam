import { Modal, Button } from "../ui";
import styles from "./DeleteConfirmModal.module.css";

export interface DeleteConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  collectionName: string;
  isLoading?: boolean;
}

/**
 * Confirmation modal for deleting a collection.
 */
export function DeleteConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  collectionName,
  isLoading = false,
}: DeleteConfirmModalProps) {
  async function handleConfirm() {
    await onConfirm();
    onClose();
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Delete Collection"
      footer={
        <div className={styles.footer}>
          <div />
          <div className={styles.actions}>
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleConfirm}
              isLoading={isLoading}
              leftIcon={<TrashIcon />}
            >
              Delete
            </Button>
          </div>
        </div>
      }
    >
      <div className={styles.content}>
        <p className={styles.message}>
          Are you sure you want to delete{" "}
          <strong>&quot;{collectionName}&quot;</strong>? This action cannot be
          undone.
        </p>
        <p className={styles.warning}>
          All feeds associated with this collection will be removed from it.
        </p>
      </div>
    </Modal>
  );
}

function TrashIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <line x1="10" y1="11" x2="10" y2="17" />
      <line x1="14" y1="11" x2="14" y2="17" />
    </svg>
  );
}
